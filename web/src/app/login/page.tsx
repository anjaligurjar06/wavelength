export default function LoginPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-2xl font-semibold">Wavelength</h1>
      <p className="text-sm text-neutral-500">
        Connect your Spotify account to find your match.
      </p>
      <a      
        href={`${apiUrl}/auth/spotify/authorize`}
        className="rounded-full bg-green-500 px-6 py-3 font-medium text-white hover:bg-green-600"
      >
        Connect with Spotify
      </a>
    </main>
  );
}

