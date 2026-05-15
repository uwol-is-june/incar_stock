export default async function handler(req, res) {
  // Vercel Cron은 GET 요청을 사용하므로 POST 제한 제거
  // CRON_SECRET으로 인증 (Vercel이 cron 요청 시 Authorization 헤더에 자동 주입)
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret && req.headers.authorization !== `Bearer ${cronSecret}`) {
    return res.status(401).end('Unauthorized');
  }

  const token = process.env.GITHUB_TOKEN;
  if (!token) return res.status(500).json({ error: 'GITHUB_TOKEN not configured' });

  const r = await fetch(
    'https://api.github.com/repos/uwol-is-june/incar_stock/actions/workflows/daily-collect.yml/dispatches',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/vnd.github+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ref: 'main' }),
    }
  );

  res.status(r.status === 204 ? 200 : r.status).json({ ok: r.status === 204 });
}
