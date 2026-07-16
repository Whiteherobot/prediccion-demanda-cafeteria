import { definePreset } from '@primeuix/themes';
import Aura from '@primeuix/themes/aura';
import { PRIMARY_SCALE } from './brand-tokens';

/**
 * Preset de PrimeNG para ECQTC.
 * Base Aura + paleta primary de la marca (#B2A0B0).
 * El color de "primary" alimenta botones, links, focus, etc.
 */
export const EcqtcPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: PRIMARY_SCALE[50],
      100: PRIMARY_SCALE[100],
      200: PRIMARY_SCALE[200],
      300: PRIMARY_SCALE[300],
      400: PRIMARY_SCALE[400],
      500: PRIMARY_SCALE[500],
      600: PRIMARY_SCALE[600],
      700: PRIMARY_SCALE[700],
      800: PRIMARY_SCALE[800],
      900: PRIMARY_SCALE[900],
      950: PRIMARY_SCALE[950],
    },
    colorScheme: {
      light: {
        primary: {
          color: '{primary.700}',
          contrastColor: '#ffffff',
          hoverColor: '{primary.800}',
          activeColor: '{primary.900}',
        },
      },
    },
  },
});
