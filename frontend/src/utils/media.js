import api from "../api/axios";

export const buildAbsoluteMediaUrl = (value) => {
  if (!value) return null;
  if (/^https?:\/\//i.test(value)) return value;

  const baseURL = api?.defaults?.baseURL || "";
  if (!baseURL) return value;

  const normalizedBase = baseURL.endsWith("/") ? baseURL.slice(0, -1) : baseURL;
  const normalizedPath = value.startsWith("/") ? value : `/${value}`;

  return `${normalizedBase}${normalizedPath}`;
};
