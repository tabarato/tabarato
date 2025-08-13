export default function getEnvVar(key) {
  switch (key) {
    case "API_URL":
      return import.meta.env.VITE_API_URL;
    default:
      return undefined;
  }
}