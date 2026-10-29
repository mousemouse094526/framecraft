// Starts the backend for `npm run dev` with the venv's own Python, not
// `uv run`: right after setup, the terminal may not see uv on PATH yet.
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const windows = process.platform === "win32";
const python = windows
  ? join(root, ".venv", "Scripts", "python.exe")
  : join(root, ".venv", "bin", "python");

if (!existsSync(python)) {
  console.error(`ยังไม่ได้ติดตั้ง: รัน ${windows ? "setup.cmd" : "./setup.sh"} ก่อน`);
  process.exit(1);
}

const api = spawn(
  python,
  ["-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", "8000"],
  { cwd: root, stdio: "inherit" },
);
// No signal forwarding: on Ctrl+C concurrently signals this whole process
// tree (tree-kill), uvicorn included.
api.on("exit", (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
