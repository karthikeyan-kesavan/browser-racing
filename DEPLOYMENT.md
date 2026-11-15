# Host Browser Racing on Render

The project includes a Render Blueprint in `render.yaml`. Render can build and host the game directly from a GitHub repository.

## Deploy

1. Create a GitHub repository and push this project to it.
2. Sign in at <https://render.com> with GitHub.
3. In the Render dashboard, select **New**, then **Blueprint**.
4. Connect the GitHub repository containing this project.
5. Confirm the `browser-racing` service and select **Deploy Blueprint**.
6. When deployment finishes, open the public `https://browser-racing-....onrender.com` URL shown by Render.

Render automatically installs `requirements.txt`, starts Gunicorn on the assigned port, and checks `/health`. Future pushes to the connected branch deploy automatically.

## Pulse Arena online rooms

Push the updated game files, including `game/pulse.py`, `templates/pulse_arena.html`,
`server.py`, `requirements.txt`, and `render.yaml`, to the branch connected to Render.
Do not deploy only the HTML: online matches need the Python room server.

The start command must be:

```text
gunicorn --workers 1 --threads 100 --timeout 120 --bind 0.0.0.0:$PORT server:app
```

Use **one worker and one service instance**. Rooms live in that process's memory;
multiple workers or instances would split players across different room servers.
`simple-websocket` enables WebSockets with the threaded worker. Use a Render
**Web Service**, not a static site.

After deployment, share `https://YOUR-SERVICE.onrender.com/pulse-arena`.
Select **Play Online with Friends**, create a room, and share the generated invite
link or six-character code. Friends open the same hosted game from their own
computers and join. The host starts rounds; bots fill unused slots up to six.
**Play with Bots** starts an independent solo game instead.

To verify the deployment, open `/health`, then join one room from two browsers or
computers. Both should see the same contenders, ball, and eliminations. Creating a
different room should not show the first room's players.

### Using pulsearena.com

`pulsearena.com` is not automatically registered or published by this project.
You must own the domain and have access to its DNS settings.

1. First deploy and verify the generated `onrender.com` game URL.
2. In the Render service's **Settings > Custom Domains**, add `pulsearena.com`.
3. At your domain provider, apply the DNS records shown by Render. Remove
   conflicting `AAAA` records as instructed by Render.
4. Return to Render and verify the domain. Wait for its HTTPS certificate.
5. Share `https://pulsearena.com/pulse-arena` only after it loads successfully.

Render manages HTTPS certificates and redirects HTTP to HTTPS; Socket.IO uses
the current site's origin, so online rooms work on the custom domain without a
hard-coded server URL.

See [Render's Flask deployment guide](https://render.com/docs/deploy-flask),
[WebSocket guidance](https://render.com/docs/websocket), and
[custom-domain setup](https://render.com/docs/custom-domains).

## Notes

- The free Render plan may sleep after inactivity, so its first load can take about a minute.
- Garage progress is stored in each player's browser. Deploying a new game version does not erase it.
- Three.js, cannon-es, fonts, and the optional detailed car model use public CDNs, so players need internet access.
- The Render service name must be unique. Render will offer a different public URL if `browser-racing` is already taken.
- Online rooms disappear on server restart or deployment. If a player disconnects,
  their contender becomes a bot and the host role transfers to another connected
  player. The last player leaving removes the room.
- Online rounds cannot be paused for everyone. Opening your menu stops your input
  but the match keeps running; use the shop between rounds.
- Coins and purchases stay in each browser, not in an online account. Different
  devices and different site origins have separate progress.
- The solo 2D game needs no external assets. Online mode loads the Socket.IO
  client from `cdn.socket.io`; a failed connection is reported rather than
  silently switching to bots.