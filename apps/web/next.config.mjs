const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiUrl}/api/:path*` }];
  },
};
