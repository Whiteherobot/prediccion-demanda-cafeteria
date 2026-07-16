export interface RecetaInsumo {
  insumo: string;
  cantidad: number;
  unidad: 'g' | 'ml' | 'u';
}

/**
 * Insumos: NOMBRES reales, tomados de `catalogo_productos_con_insumos.csv`
 * (catálogo real de El Café Que Te Conté, provisto 2026-07-16). CANTIDADES:
 * siguen siendo una estimación — el catálogo lista qué insumos lleva cada
 * producto, pero no las cantidades por unidad vendida, así que eso se
 * mantiene estimado hasta que el café lo confirme.
 *
 * 32/33 productos tienen match directo o por unión de variantes con el
 * catálogo (ver `PRODUCTOS_SIN_CATALOGO` para el único que no: "Cómo en Casa",
 * que en el dataset de ventas es un producto en sí mismo — no una categoría —
 * y no aparece como fila en el catálogo).
 *
 * Casos especiales de Bebidas (el dataset de ventas agrupa por `producto`,
 * más grueso que las variantes por sabor del catálogo):
 * - Agua = unión de "Purificada" + "Con gas" (mismo insumo, dos presentaciones).
 * - Café = unión de Americano/Capuchino/Mocachino/Café Frío/Mocca — se usa el
 *   perfil más común (Café + Leche, 4/5 variantes) como receta representativa.
 * - Gaseosas = unión de Coca-Cola/Fanta/Inca Kola/Tropical (mismo patrón, sabor distinto).
 * - Jugos = variantes con "Fruta + Agua" (Naranja/Mora/Frutilla, precio 3.5).
 * - Smoothies = variantes con "Fruta + Yogurt + Hielo" (mismos sabores, precio 4.5).
 * - Frappé = INFERIDO: el catálogo no tiene una fila llamada "Frappé"; la única
 *   fila de Bebidas sin producto correspondiente en el dataset es "Fresa"
 *   (Fresa, Hielo, Leche), así que se asume que es el mismo ítem. Validar con
 *   el café — es la única inferencia de nombre en todo el mapeo, el resto son
 *   matches directos por nombre de producto.
 */
export const RECETAS: Record<number, RecetaInsumo[]> = {
  // Bebidas
  2: [{ insumo: 'Agua embotellada (purificada / con gas)', cantidad: 1, unidad: 'u' }], // Agua
  7: [
    { insumo: 'Café molido', cantidad: 18, unidad: 'g' },
    { insumo: 'Leche', cantidad: 150, unidad: 'ml' },
  ], // Café
  12: [
    { insumo: 'Fresa', cantidad: 100, unidad: 'g' },
    { insumo: 'Hielo', cantidad: 100, unidad: 'g' },
    { insumo: 'Leche', cantidad: 150, unidad: 'ml' },
  ], // Frappé (inferido de "Fresa" en el catálogo, ver nota arriba)
  15: [{ insumo: 'Gaseosa (Coca-Cola / Fanta / Inca Kola / Tropical)', cantidad: 1, unidad: 'u' }], // Gaseosas
  18: [
    { insumo: 'Fruta fresca', cantidad: 150, unidad: 'g' },
    { insumo: 'Agua', cantidad: 100, unidad: 'ml' },
  ], // Jugos
  28: [
    { insumo: 'Fruta fresca', cantidad: 120, unidad: 'g' },
    { insumo: 'Yogurt', cantidad: 150, unidad: 'ml' },
    { insumo: 'Hielo', cantidad: 80, unidad: 'g' },
  ], // Smoothies

  // Desayunos
  3: [
    { insumo: 'Pan', cantidad: 80, unidad: 'g' },
    { insumo: 'Aguacate', cantidad: 100, unidad: 'g' },
    { insumo: 'Huevo', cantidad: 1, unidad: 'u' },
  ], // Avocado Toast
  4: [
    { insumo: 'Pan', cantidad: 80, unidad: 'g' },
    { insumo: 'Tocino', cantidad: 40, unidad: 'g' },
    { insumo: 'Huevo', cantidad: 1, unidad: 'u' },
    { insumo: 'Queso', cantidad: 30, unidad: 'g' },
  ], // Bacon Egg and Cheese
  16: [
    { insumo: 'Pan', cantidad: 80, unidad: 'g' },
    { insumo: 'Jamón', cantidad: 40, unidad: 'g' },
    { insumo: 'Queso', cantidad: 30, unidad: 'g' },
  ], // Ham and Cheese
  29: [
    { insumo: 'Plátano Verde', cantidad: 150, unidad: 'g' },
    { insumo: 'Queso', cantidad: 40, unidad: 'g' },
    { insumo: 'Huevo', cantidad: 1, unidad: 'u' },
  ], // Tigrillo Patacón

  // Galletas
  10: [
    { insumo: 'Harina', cantidad: 60, unidad: 'g' },
    { insumo: 'Chocolate', cantidad: 20, unidad: 'g' },
  ], // Chispas de Chocolate
  14: [
    { insumo: 'Harina', cantidad: 60, unidad: 'g' },
    { insumo: 'Nuez', cantidad: 20, unidad: 'g' },
  ], // Galleta de Nuez
  21: [
    { insumo: 'Harina', cantidad: 60, unidad: 'g' },
    { insumo: 'Oreo', cantidad: 25, unidad: 'g' },
  ], // New York Oreo
  22: [
    { insumo: 'Harina', cantidad: 60, unidad: 'g' },
    { insumo: 'Tres Chocolates', cantidad: 30, unidad: 'g' },
  ], // New York Triple Chocolate
  27: [
    { insumo: 'Harina', cantidad: 60, unidad: 'g' },
    { insumo: 'Cacao', cantidad: 15, unidad: 'g' },
    { insumo: 'Colorante', cantidad: 2, unidad: 'g' },
  ], // Red Velvet
  32: [
    { insumo: 'Harina', cantidad: 60, unidad: 'g' },
    { insumo: 'Tres Chocolates', cantidad: 30, unidad: 'g' },
  ], // Triple Chocolate

  // Para Compartir
  1: [
    { insumo: 'Galleta', cantidad: 120, unidad: 'g' },
    { insumo: 'Helado', cantidad: 80, unidad: 'g' },
    { insumo: 'Café', cantidad: 30, unidad: 'ml' },
  ], // Affo Cookie
  5: [
    { insumo: 'Pan', cantidad: 80, unidad: 'g' },
    { insumo: 'Banano', cantidad: 100, unidad: 'g' },
    { insumo: 'Nutella', cantidad: 30, unidad: 'g' },
  ], // Bananella Toast
  6: [
    { insumo: 'Brownie', cantidad: 100, unidad: 'g' },
    { insumo: 'Helado', cantidad: 80, unidad: 'g' },
    { insumo: 'Salsa', cantidad: 30, unidad: 'g' },
  ], // Break Your Diet
  13: [
    { insumo: 'Cacao', cantidad: 40, unidad: 'g' },
    { insumo: 'Harina', cantidad: 80, unidad: 'g' },
    { insumo: 'Azúcar', cantidad: 40, unidad: 'g' },
  ], // Fudgy Brownies
  17: [
    { insumo: 'Galleta', cantidad: 60, unidad: 'g' },
    { insumo: 'Helado', cantidad: 100, unidad: 'g' },
    { insumo: 'Nutella', cantidad: 40, unidad: 'g' },
  ], // Helado y Nutella
  19: [
    { insumo: 'Galleta', cantidad: 60, unidad: 'g' },
    { insumo: 'Maní', cantidad: 60, unidad: 'g' },
    { insumo: 'Almendras', cantidad: 60, unidad: 'g' },
  ], // Maní y Almendras
  20: [
    { insumo: 'Brownie', cantidad: 80, unidad: 'g' },
    { insumo: 'Helado', cantidad: 80, unidad: 'g' },
    { insumo: 'Café', cantidad: 30, unidad: 'ml' },
  ], // Negrito Affogato
  23: [
    { insumo: 'Pan', cantidad: 90, unidad: 'g' },
    { insumo: 'Nutella', cantidad: 40, unidad: 'g' },
    { insumo: 'Huevo', cantidad: 1, unidad: 'u' },
    { insumo: 'Leche', cantidad: 50, unidad: 'ml' },
  ], // Nutella French Toast
  24: [
    { insumo: 'Galleta', cantidad: 60, unidad: 'g' },
    { insumo: 'Nutella', cantidad: 40, unidad: 'g' },
    { insumo: 'Maní', cantidad: 30, unidad: 'g' },
  ], // Nutella Maní
  25: [
    { insumo: 'Plátano Verde', cantidad: 150, unidad: 'g' },
    { insumo: 'Carne', cantidad: 80, unidad: 'g' },
    { insumo: 'Salsa', cantidad: 20, unidad: 'g' },
  ], // Patacón Crunch
  26: [
    { insumo: 'Pan', cantidad: 80, unidad: 'g' },
    { insumo: 'Tomate', cantidad: 40, unidad: 'g' },
    { insumo: 'Queso', cantidad: 50, unidad: 'g' },
    { insumo: 'Pepperoni', cantidad: 30, unidad: 'g' },
  ], // Pizza Toast

  // Pasteles
  8: [
    { insumo: 'Queso Crema', cantidad: 120, unidad: 'g' },
    { insumo: 'Frutos Rojos', cantidad: 40, unidad: 'g' },
  ], // Cheesecake de Frutos Rojos
  9: [
    { insumo: 'Queso Crema', cantidad: 120, unidad: 'g' },
    { insumo: 'Limón', cantidad: 20, unidad: 'g' },
  ], // Cheesecake de Limón
  30: [
    { insumo: 'Cacao', cantidad: 30, unidad: 'g' },
    { insumo: 'Harina', cantidad: 100, unidad: 'g' },
    { insumo: 'Leche', cantidad: 60, unidad: 'ml' },
  ], // Torta Mojada de Chocolate
  31: [
    { insumo: 'Harina', cantidad: 100, unidad: 'g' },
    { insumo: 'Tres Leches', cantidad: 60, unidad: 'ml' },
  ], // Tres Leches
  33: [
    { insumo: 'Vainilla', cantidad: 20, unidad: 'g' },
    { insumo: 'Harina', cantidad: 100, unidad: 'g' },
    { insumo: 'Mermelada', cantidad: 30, unidad: 'g' },
  ], // Vainilla con Relleno de Mermelada

  // Sin match en el catálogo — sigue 100% estimado (ver PRODUCTOS_SIN_CATALOGO)
  11: [
    { insumo: 'Pan', cantidad: 80, unidad: 'g' },
    { insumo: 'Huevo', cantidad: 1, unidad: 'u' },
    { insumo: 'Queso', cantidad: 30, unidad: 'g' },
    { insumo: 'Jamón', cantidad: 30, unidad: 'g' },
  ], // Cómo en Casa
};

/** product_id sin fila propia en `catalogo_productos_con_insumos.csv` — receta 100% estimada. */
export const PRODUCTOS_SIN_CATALOGO = new Set<number>([11]);
