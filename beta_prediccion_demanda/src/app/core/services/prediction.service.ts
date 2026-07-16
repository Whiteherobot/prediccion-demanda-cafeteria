import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  BusinessMetricsResponse,
  ExplainRequest,
  ExplainResponse,
  ModelInfoResponse,
  PredictRequest,
  PredictResponse,
  ReentrenarResponse,
  ReporteDemandaResponse,
} from '../models/prediction.model';

/** Cliente de la API real de Práctica 3 (SVR multi-horizonte). Arrancar con `make api` (puerto 8000). */
@Injectable({ providedIn: 'root' })
export class PredictionService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000';

  modelInfo(): Observable<ModelInfoResponse> {
    return this.http.get<ModelInfoResponse>(`${this.baseUrl}/model/info`);
  }

  predict(req: PredictRequest): Observable<PredictResponse> {
    return this.http.post<PredictResponse>(`${this.baseUrl}/predict`, req);
  }

  /** Predicción para varios productos a la vez (un request /predict/batch). */
  predictBatch(items: PredictRequest[]): Observable<{ resultados: PredictResponse[] }> {
    return this.http.post<{ resultados: PredictResponse[] }>(`${this.baseUrl}/predict/batch`, {
      items,
    });
  }

  /** Ahorro real del modelo vs. baseline ingenuo + factores globales (metrics/metrics.json). */
  businessMetrics(): Observable<BusinessMetricsResponse> {
    return this.http.get<BusinessMetricsResponse>(`${this.baseUrl}/metrics/negocio`);
  }

  /** Explicación SHAP on-demand de una predicción puntual (drill-down por producto). */
  explain(req: ExplainRequest): Observable<ExplainResponse> {
    return this.http.post<ExplainResponse>(`${this.baseUrl}/predict/explain`, req);
  }

  /** Reporte conciso: producto con más demanda de cara a la semana (proyección real
   * a t+7) y de cara al mes (histórico real de los últimos 30 días). */
  reporteDemanda(fecha: string): Observable<ReporteDemandaResponse> {
    return this.http.get<ReporteDemandaResponse>(`${this.baseUrl}/reportes/demanda-periodo`, {
      params: { fecha },
    });
  }

  /** Sube un CSV de ventas nuevas y reentrena los modelos (multipart/form-data). */
  reentrenar(file: File): Observable<ReentrenarResponse> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<ReentrenarResponse>(`${this.baseUrl}/admin/reentrenar`, form);
  }
}
