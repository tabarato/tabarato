export default function getEnvVar(key) {
  switch (key) {
    case "ROUTES_API_KEY":
      return import.meta.env.VITE_ROUTES_API_KEY;
    case "ROUTES_API_URL":
      return import.meta.env.VITE_ROUTES_API_URL;
    case "API_URL":
      return import.meta.env.VITE_API_URL;
    default:
      return undefined;
  }
}