/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: '100gb',
    },
  },
  async redirects() {
    return [
      {
        source: '/api-docs',
        destination: `${process.env.FASTAPI_URL ?? 'http://localhost:8000'}/docs`,
        permanent: false,
      },
      {
        // The eval business is now the homepage; keep old /evaluate links working.
        source: '/evaluate',
        destination: '/',
        permanent: true,
      },
    ]
  },
  async rewrites() {
    // Serve the static clinician recruitment page at a clean /clinicians URL.
    return [
      { source: '/clinicians', destination: '/clinicians.html' },
    ]
  },
}

export default nextConfig
