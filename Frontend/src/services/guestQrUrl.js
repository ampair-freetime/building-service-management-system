export function buildGuestQrUrl(baseUrl, token) {
  let locationToken = token.trim();
  if (/^https?:\/\//i.test(locationToken)) {
    locationToken = new URL(locationToken).searchParams.get("token")?.trim() ?? "";
  }
  if (!locationToken) throw new Error("กรุณาระบุ token ของสถานที่");
  const url = new URL(baseUrl);
  url.search = "";
  url.hash = "";
  if (!/\/user\/?$/.test(url.pathname)) {
    url.pathname = /\/(?:cleaning|repair|report)\/?$/.test(url.pathname)
      ? url.pathname.replace(/\/(?:cleaning|repair|report)\/?$/, "/user")
      : `${url.pathname.replace(/\/?$/, "/")}user`;
  }
  url.searchParams.set("token", locationToken);
  return url.toString();
}
