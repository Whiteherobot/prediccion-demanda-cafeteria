export interface PredictRequest {
  product_id: number;
  fecha: string;
  horizonte: number;
}

export interface PredictResponse {
  product_id: number;
  fecha_solicitada: string;
  fecha_referencia_datos: string;
  fecha_objetivo: string;
  horizonte_dias: number;
  prediccion_esperada: number;
  escenario_conservador: number;
  escenario_optimista: number;
  nivel_riesgo: 'verde' | 'amarillo' | 'rojo' | string;
  alerta_alta_demanda: boolean;
  alerta_anomalia: boolean;
  datos_historicos_suficientes: boolean;
}

export interface RangoFechasResponse {
  min: string;
  max: string;
  min_valido_referencia: string;
}

export interface ModelInfoResponse {
  features_svr: string[];
  features_svc_iso: string[];
  horizontes_soportados: number[];
  metricas: Record<string, { rmse: number; mae: number; r2: number }>;
  calidad_datos_por_producto: Record<string, boolean>;
  rango_fechas: RangoFechasResponse;
}

export interface BusinessMetricsResponse {
  ingresos_en_riesgo_baseline_ingenuo: number;
  ingresos_en_riesgo_modelo: number;
  reduccion_pct: number;
  importancia_variables_top5: Record<string, number>;
}

export interface ExplainRequest {
  product_id: number;
  fecha: string;
  horizonte: number;
}

export interface ExplainFactor {
  concepto_negocio: string;
  shap: number;
}

export interface ExplainResponse {
  product_id: number;
  fecha_referencia_datos: string;
  prediccion_h: number;
  base_value: number;
  factores: ExplainFactor[];
}

export interface ReporteProductoItem {
  product_id: number;
  nombre: string;
  proyeccion_7dias: number | null;
  historico_30dias: number;
}

export interface ReporteDemandaResponse {
  fecha_referencia: string;
  top_semana: ReporteProductoItem | null;
  top_mes: ReporteProductoItem;
  items: ReporteProductoItem[];
}

export interface ReentrenarResponse {
  filas_nuevas_agregadas: number;
  filas_totales_ventas: number;
  rango_fechas: string;
  metricas: Record<string, { rmse: number; mae: number; r2: number }>;
  reduccion_pct_ingresos_riesgo: number;
  backup_creado: string;
  nota: string;
}
