module.exports = {
  apps: [
    {
      name: "finnkino",
      cwd: "/home/asad/projects/finnkino-seatmap",
      script: "app.py",
      interpreter: "/home/asad/projects/finnkino-seatmap/.venv/bin/python3",
      env: {
        PORT: "3004",
      },
      max_restarts: 10,
      restart_delay: 3000,
    },
  ],
};
