export interface Product {
  id: number;
  nombre: string;
}

/** product_id → nombre, asignado por orden alfabético (data/processed/dataset_features.parquet). */
export const PRODUCTS: Product[] = [
  { id: 1, nombre: 'Affo Cookie' },
  { id: 2, nombre: 'Agua' },
  { id: 3, nombre: 'Avocado Toast' },
  { id: 4, nombre: 'Bacon Egg and Cheese' },
  { id: 5, nombre: 'Bananella Toast' },
  { id: 6, nombre: 'Break Your Diet' },
  { id: 7, nombre: 'Café' },
  { id: 8, nombre: 'Cheesecake de Frutos Rojos' },
  { id: 9, nombre: 'Cheesecake de Limón' },
  { id: 10, nombre: 'Chispas de Chocolate' },
  { id: 11, nombre: 'Cómo en Casa' },
  { id: 12, nombre: 'Frappé' },
  { id: 13, nombre: 'Fudgy Brownies' },
  { id: 14, nombre: 'Galleta de Nuez' },
  { id: 15, nombre: 'Gaseosas' },
  { id: 16, nombre: 'Ham and Cheese' },
  { id: 17, nombre: 'Helado y Nutella' },
  { id: 18, nombre: 'Jugos' },
  { id: 19, nombre: 'Maní y Almendras' },
  { id: 20, nombre: 'Negrito Affogato' },
  { id: 21, nombre: 'New York Oreo' },
  { id: 22, nombre: 'New York Triple Chocolate' },
  { id: 23, nombre: 'Nutella French Toast' },
  { id: 24, nombre: 'Nutella Maní' },
  { id: 25, nombre: 'Patacón Crunch' },
  { id: 26, nombre: 'Pizza Toast' },
  { id: 27, nombre: 'Red Velvet' },
  { id: 28, nombre: 'Smoothies' },
  { id: 29, nombre: 'Tigrillo Patacón' },
  { id: 30, nombre: 'Torta Mojada de Chocolate' },
  { id: 31, nombre: 'Tres Leches' },
  { id: 32, nombre: 'Triple Chocolate' },
  { id: 33, nombre: 'Vainilla con Relleno de Mermelada' },
];
