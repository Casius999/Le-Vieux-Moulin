import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Import des ressources de traduction
import frTranslation from './locales/fr.json';
import enTranslation from './locales/en.json';

// Configuration de i18next
i18n
  .use(initReactI18next) // Passe i18n en dessous à react-i18next
  .init({
    resources: {
      fr: {
        translation: frTranslation
      },
      en: {
        translation: enTranslation
      }
    },
    lng: 'fr', // Langue par défaut
    fallbackLng: 'fr', // Langue de secours
    interpolation: {
      escapeValue: false // React échape déjà les valeurs
    },
    react: {
      useSuspense: false // Désactive le suspense pour éviter des problèmes avec le SSR
    }
  });

export default i18n;
