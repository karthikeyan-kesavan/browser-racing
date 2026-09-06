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

## Notes

- The free Render plan may sleep after inactivity, so its first load can take about a minute.
- Garage progress is stored in each player's browser. Deploying a new game version does not erase it.
- Three.js, cannon-es, fonts, and the optional detailed car model use public CDNs, so players need internet access.
- The Render service name must be unique. Render will offer a different public URL if `browser-racing` is already taken.