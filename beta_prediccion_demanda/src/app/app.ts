import { DecimalPipe, TitleCasePipe } from '@angular/common';
import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ChartModule } from 'primeng/chart';

import { FEATURE_LABELS } from './core/data/feature-labels';
import { PRODUCTS } from './core/data/products';
import { PRODUCTOS_SIN_CATALOGO, RECETAS } from './core/data/recipes';
import {
  BusinessMetricsResponse,
  ExplainResponse,
  ModelInfoResponse,
  PredictResponse,
  ReentrenarResponse,
  ReporteDemandaResponse,
} from './core/models/prediction.model';
import { PredictionService } from './core/services/prediction.service';

const RIESGO_CLASE: Record<string, string> = {
  verde: 'bg-brand-accent/10 text-brand-accent',
  amarillo: 'bg-amber-100 text-amber-700',
  rojo: 'bg-red-100 text-red-700',
};

/** Nombres en criollo del horizonte de predicción — nada de "t+N" a la vista del cliente. */
const HORIZONTE_LABELS: Record<number, string> = {
  1: 'mañana',
  3: 'en 3 días',
  7: 'en una semana',
};

// Valores por defecto mientras carga /model/info (que trae el rango real —
// el SVR necesita 14 días previos para `rolling_mean_14`, así que el mínimo
// válido no es el primer día del dataset, y el máximo cambia si se reentrena).
const FECHA_MIN = '2026-04-16';
const FECHA_MAX = '2026-07-31';
const AUTOPLAY_MS = 2200;

/** Beta standalone — misma estética del ECQTC (pantalla "Predicción de preparación"),
 * pero conectada a la API real del SVR multi-horizonte de Práctica 3. Solo para
 * probar la integración de forma aislada, no forma parte del repo del ECQTC. */
@Component({
  selector: 'app-root',
  imports: [ChartModule, FormsModule, DecimalPipe, TitleCasePipe],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit, OnDestroy {
  private readonly api = inject(PredictionService);

  readonly fecha = signal(FECHA_MAX);
  readonly horizonte = signal(1);
  readonly horizontesDisponibles = signal<number[]>([1, 3, 7]);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly resultados = signal<PredictResponse[]>([]);
  readonly modelInfo = signal<ModelInfoResponse | null>(null);
  readonly businessMetrics = signal<BusinessMetricsResponse | null>(null);

  /** Rango real de fechas servido por /model/info (se actualiza tras reentrenar). */
  readonly fechaMin = computed(() => this.modelInfo()?.rango_fechas.min_valido_referencia ?? FECHA_MIN);
  readonly fechaMax = computed(() => this.modelInfo()?.rango_fechas.max ?? FECHA_MAX);

  readonly reporte = signal<ReporteDemandaResponse | null>(null);
  readonly reporteLoading = signal(false);

  readonly reentrenando = signal(false);
  readonly reentrenarResultado = signal<ReentrenarResponse | null>(null);
  readonly reentrenarError = signal<string | null>(null);

  readonly playing = signal(false);
  private playTimer: ReturnType<typeof setInterval> | null = null;

  readonly confirmados = signal<Set<number>>(new Set());
  readonly toastMsg = signal<string | null>(null);
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  readonly selectedProduct = signal<PredictResponse | null>(null);
  readonly explainData = signal<ExplainResponse | null>(null);
  readonly explainLoading = signal(false);
  readonly explainError = signal<string | null>(null);

  /** Sección aparte para probar solo productos puntuales — no toca `resultados()`
   * ni el resto de la pantalla (sugerencias, insumos, reporte, gráfico). */
  readonly productos = PRODUCTS;
  readonly productosSeleccionados = signal<Set<number>>(new Set());
  readonly pruebaLoading = signal(false);
  readonly pruebaError = signal<string | null>(null);
  readonly pruebaResultados = signal<PredictResponse[]>([]);

  readonly nombrePorId = new Map(PRODUCTS.map((p) => [p.id, p.nombre]));

  readonly ordenados = computed(() =>
    [...this.resultados()].sort((a, b) => b.prediccion_esperada - a.prediccion_esperada),
  );

  readonly topProducts = computed(() => this.ordenados().slice(0, 8));
  readonly sugerencias = computed(() => this.ordenados().slice(0, 6));

  /** Insumos agregados = predicción real (SVR) × receta (nombres reales del catálogo del café,
   * cantidades por unidad estimadas — ver core/data/recipes.ts). */
  readonly insumosEstimados = computed(() => {
    const totales = new Map<string, { insumo: string; unidad: string; cantidad: number }>();
    for (const r of this.resultados()) {
      const receta = RECETAS[r.product_id];
      if (!receta) continue;
      for (const item of receta) {
        const key = `${item.insumo}__${item.unidad}`;
        const suma = r.prediccion_esperada * item.cantidad;
        const prev = totales.get(key);
        if (prev) {
          prev.cantidad += suma;
        } else {
          totales.set(key, { insumo: item.insumo, unidad: item.unidad, cantidad: suma });
        }
      }
    }
    return [...totales.values()].sort((a, b) => b.cantidad - a.cantidad).slice(0, 10);
  });

  readonly productosSinReceta = computed(
    () => this.resultados().filter((r) => PRODUCTOS_SIN_CATALOGO.has(r.product_id)).length,
  );

  readonly factoresGlobales = computed(() => {
    const info = this.businessMetrics();
    if (!info) return [];
    return Object.entries(info.importancia_variables_top5)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([feature, peso]) => ({
        etiqueta: FEATURE_LABELS[feature] ?? feature,
        peso,
      }));
  });

  readonly topData = computed(() => {
    const top = this.topProducts();
    return {
      labels: top.map((r) => this.nombrePorId.get(r.product_id) ?? `#${r.product_id}`),
      datasets: [
        {
          label: 'Predicción de unidades',
          data: top.map((r) => Math.round(r.prediccion_esperada * 10) / 10),
          backgroundColor: '#b2a0b0',
          borderRadius: 6,
        },
      ],
    };
  });

  readonly topOptions = {
    indexAxis: 'y' as const,
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 400 },
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { font: { size: 11 }, color: '#8a7a85' }, grid: { color: 'rgba(178,160,176,0.15)' } },
      y: { grid: { display: false }, ticks: { font: { size: 11 }, color: '#8a7a85' } },
    },
  };

  ngOnInit(): void {
    this.cargarModelInfo();
    this.api.businessMetrics().subscribe({
      next: (info) => this.businessMetrics.set(info),
      error: () => {
        /* KPI de negocio es un extra visual, no bloquea el resto de la pantalla */
      },
    });
    this.cargar();
  }

  private cargarModelInfo(): void {
    this.api.modelInfo().subscribe({
      next: (info) => {
        this.modelInfo.set(info);
        this.horizontesDisponibles.set(info.horizontes_soportados);
        // Si el rango real (p. ej. tras reentrenar) dejó la fecha actual afuera, la reencuadra.
        if (this.fecha() > info.rango_fechas.max) this.fecha.set(info.rango_fechas.max);
        if (this.fecha() < info.rango_fechas.min_valido_referencia) {
          this.fecha.set(info.rango_fechas.min_valido_referencia);
        }
      },
      error: () => {
        /* si /model/info falla, cargar() de abajo ya reporta el error de conexión */
      },
    });
  }

  ngOnDestroy(): void {
    this.stopPlay();
    if (this.toastTimer) clearTimeout(this.toastTimer);
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.confirmados.set(new Set());
    const items = PRODUCTS.map((p) => ({
      product_id: p.id,
      fecha: this.fecha(),
      horizonte: this.horizonte(),
    }));
    this.api.predictBatch(items).subscribe({
      next: (res) => {
        this.resultados.set(res.resultados);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.resultados.set([]);
        this.stopPlay();
        this.error.set(
          err.status === 0
            ? 'No se pudo conectar con la API de Práctica 3. Levantala con `make api` (puerto 8000) y volvé a intentar.'
            : `Error ${err.status}: ${err.error?.detail ?? 'la API devolvió un error.'}`,
        );
      },
    });
    this.cargarReporte();
  }

  private cargarReporte(): void {
    this.reporteLoading.set(true);
    this.api.reporteDemanda(this.fecha()).subscribe({
      next: (r) => {
        this.reporte.set(r);
        this.reporteLoading.set(false);
      },
      error: () => {
        this.reporteLoading.set(false);
        /* el reporte es un extra, no bloquea el resto de la pantalla */
      },
    });
  }

  /** Sube un CSV de ventas nuevas (mismo esquema de `ventas.csv`) y reentrena los modelos. */
  onCsvSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    this.reentrenando.set(true);
    this.reentrenarError.set(null);
    this.reentrenarResultado.set(null);
    this.api.reentrenar(file).subscribe({
      next: (res) => {
        this.reentrenando.set(false);
        this.reentrenarResultado.set(res);
        this.showToast(`Reentrenado: +${res.filas_nuevas_agregadas} filas nuevas`);
        this.cargarModelInfo();
        this.api.businessMetrics().subscribe({ next: (info) => this.businessMetrics.set(info) });
        this.cargar();
      },
      error: (err) => {
        this.reentrenando.set(false);
        this.reentrenarError.set(
          `Error ${err.status}: ${err.error?.detail ?? 'no se pudo reentrenar con este CSV.'}`,
        );
      },
    });
    input.value = '';
  }

  /** Mueve la fecha de referencia un día hacia adelante (vuelve al inicio del rango
   * real al llegar al final, para que el modo demo se pueda dejar corriendo en loop). */
  avanzarDia(): void {
    const actual = new Date(`${this.fecha()}T00:00:00`);
    actual.setDate(actual.getDate() + 1);
    const siguiente = actual.toISOString().slice(0, 10);
    this.fecha.set(siguiente > this.fechaMax() ? this.fechaMin() : siguiente);
    this.cargar();
  }

  togglePlay(): void {
    if (this.playing()) {
      this.stopPlay();
      return;
    }
    this.playing.set(true);
    this.playTimer = setInterval(() => this.avanzarDia(), AUTOPLAY_MS);
  }

  private stopPlay(): void {
    if (this.playTimer) {
      clearInterval(this.playTimer);
      this.playTimer = null;
    }
    this.playing.set(false);
  }

  toggleProductoPrueba(productId: number): void {
    const set = new Set(this.productosSeleccionados());
    if (set.has(productId)) {
      set.delete(productId);
    } else {
      set.add(productId);
    }
    this.productosSeleccionados.set(set);
  }

  limpiarSeleccionPrueba(): void {
    this.productosSeleccionados.set(new Set());
    this.pruebaResultados.set([]);
    this.pruebaError.set(null);
  }

  /** Predice SOLO los productos marcados en esta sección, con la fecha/horizonte
   * actuales. No toca `resultados()` ni ninguna otra parte de la pantalla. */
  probarSeleccionados(): void {
    const ids = [...this.productosSeleccionados()];
    if (ids.length === 0) return;

    this.pruebaLoading.set(true);
    this.pruebaError.set(null);
    const items = ids.map((id) => ({
      product_id: id,
      fecha: this.fecha(),
      horizonte: this.horizonte(),
    }));
    this.api.predictBatch(items).subscribe({
      next: (res) => {
        this.pruebaResultados.set(res.resultados);
        this.pruebaLoading.set(false);
      },
      error: (err) => {
        this.pruebaLoading.set(false);
        this.pruebaResultados.set([]);
        this.pruebaError.set(
          err.status === 0
            ? 'No se pudo conectar con la API.'
            : `Error ${err.status}: ${err.error?.detail ?? 'no se pudo predecir estos productos.'}`,
        );
      },
    });
  }

  toggleConfirmado(productId: number): void {
    const set = new Set(this.confirmados());
    const yaEstaba = set.has(productId);
    if (yaEstaba) {
      set.delete(productId);
    } else {
      set.add(productId);
    }
    this.confirmados.set(set);
    this.showToast(
      yaEstaba
        ? `${this.nombre(productId)} — desmarcado`
        : `${this.nombre(productId)} marcado como preparado ✓ (simulado, no persiste)`,
    );
  }

  private showToast(msg: string): void {
    this.toastMsg.set(msg);
    if (this.toastTimer) clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => this.toastMsg.set(null), 2800);
  }

  openExplain(r: PredictResponse): void {
    this.selectedProduct.set(r);
    this.explainData.set(null);
    this.explainError.set(null);
    this.explainLoading.set(true);
    this.api
      .explain({ product_id: r.product_id, fecha: this.fecha(), horizonte: this.horizonte() })
      .subscribe({
        next: (data) => {
          this.explainData.set(data);
          this.explainLoading.set(false);
        },
        error: (err) => {
          this.explainLoading.set(false);
          this.explainError.set(`Error ${err.status}: ${err.error?.detail ?? 'no se pudo explicar esta predicción.'}`);
        },
      });
  }

  closeExplain(): void {
    this.selectedProduct.set(null);
  }

  /** Cuánto pesó cada factor en el resultado, como % del total (suman ~100%) —
   * más fácil de entender para el cliente que el valor SHAP crudo. */
  factorPercent(factor: { shap: number }): number {
    const factores = this.explainData()?.factores ?? [];
    const total = factores.reduce((acc, f) => acc + Math.abs(f.shap), 0);
    return total > 0 ? (Math.abs(factor.shap) / total) * 100 : 0;
  }

  riesgoClase(nivel: string): string {
    return RIESGO_CLASE[nivel] ?? 'bg-gray-100 text-gray-600';
  }

  horizonteLabel(h: number = this.horizonte()): string {
    return HORIZONTE_LABELS[h] ?? `en ${h} días`;
  }

  nombre(id: number): string {
    return this.nombrePorId.get(id) ?? `Producto #${id}`;
  }

  /** Exporta la tabla completa (todos los productos, orden actual) a CSV, para
   * llevarla a Excel/Sheets. Client-side, no pega al backend. BOM al inicio
   * para que Excel muestre bien las tildes de los nombres reales del catálogo. */
  exportarTablaCsv(): void {
    const filas = this.ordenados();
    if (filas.length === 0) return;

    const encabezado = [
      'Producto',
      'Prediccion esperada (u.)',
      'Escenario conservador',
      'Escenario optimista',
      'Nivel de riesgo',
      'Alta demanda',
      'Fuera de lo comun',
    ];
    const lineas = filas.map((r) => [
      this.nombre(r.product_id),
      r.prediccion_esperada.toFixed(1),
      r.escenario_conservador.toFixed(1),
      r.escenario_optimista.toFixed(1),
      r.nivel_riesgo,
      r.alerta_alta_demanda ? 'si' : 'no',
      r.alerta_anomalia ? 'si' : 'no',
    ]);
    const csv = [encabezado, ...lineas]
      .map((fila) => fila.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(','))
      .join('\n');

    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `prediccion_${this.fecha()}_${this.horizonteLabel().replace(/\s+/g, '_')}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  formatInsumo(cantidad: number, unidad: string): string {
    if (unidad === 'g' && cantidad >= 1000) return `${(cantidad / 1000).toFixed(1)} kg`;
    if (unidad === 'ml' && cantidad >= 1000) return `${(cantidad / 1000).toFixed(1)} L`;
    if (unidad === 'u') return `${Math.round(cantidad)} u.`;
    return `${Math.round(cantidad)} ${unidad}`;
  }
}
