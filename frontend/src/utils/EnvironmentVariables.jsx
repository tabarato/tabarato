export default function getEnvVar(key) {
  switch (key) {
    case "ROUTES_API_KEY":
      return import.meta.env.VITE_ROUTES_API_KEY;
    case "ROUTES_API_URL":
      return import.meta.env.VITE_ROUTES_API_URL;
    case "POSTGREST_URL":
      return import.meta.env.VITE_POSTGREST_URL;
    default:
      return undefined;
  }
}