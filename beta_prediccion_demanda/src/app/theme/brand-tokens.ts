/**
 * Design tokens de marca — "El Café Que Te Conté" (ECQTC)
 * Fuente: export de Figma (cafe-app-features.md).
 *
 *  primary    #B2A0B0  Fondos principales, headers, botones primarios, tarjetas
 *  secondary  #070007  Texto principal, navbar/sidebar, contraste fuerte
 *  accent     #304429  Acentos puntuales: badges "pagado", iconos de éxito
 *  bgSoft     #F5F2F4  Fondo suave de la app
 */
export const BRAND = {
  primary: '#B2A0B0',
  secondary: '#070007',
  accent: '#304429',
  bgSoft: '#F5F2F4',
} as const;

/** Escala 50–950 derivada del primary (#B2A0B0, mauve/taupe). */
export const PRIMARY_SCALE = {
  50: '#faf8fa',
  100: '#f2eef1',
  200: '#e5dde3',
  300: '#d1c4ce',
  400: '#b2a0b0',
  500: '#9c869a',
  600: '#856f83',
  700: '#6d5a6b',
  800: '#4c3f4a',
  900: '#2f272e',
  950: '#1b161a',
} as const;

/** Escala 50–950 derivada del accent (#304429, verde). Para estados de éxito/pagado. */
export const ACCENT_SCALE = {
  50: '#f2f5f0',
  100: '#e0e8dc',
  200: '#c2d1ba',
  300: '#9cb490',
  400: '#748f66',
  500: '#547046',
  600: '#3f5734',
  700: '#304429',
  800: '#263521',
  900: '#1e2a1b',
  950: '#0f160d',
} as const;
