"""Wrapper para ejecutar Maxx_C (wpa.py) desde Antigravity mostrando la ventana de Chromium en pantalla.

1. Fuerza SW_SHOWMAXIMIZED (3) y elimina DETACHED_PROCESS exclusivamente en chrome.exe para que
   la ventana de Google Chrome for Testing aparezca siempre en la pantalla y barra de tareas.
2. Usa Win32 API (ShowWindow + SetForegroundWindow) al abrir el navegador.
3. En el paso 74.5 de `cp22-money-order`, si Hermes muestra la tarjeta de foto con cámara inválida
   ("Asegúrese que su cámara está conectada y permitida"), verifica/revive el servicio de cámara
   sintética (`scripts/camara.py`) y pulsa `Reintentar` automáticamente antes de esperar el icono válido.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import runpy
import subprocess
import sys
import time
from pathlib import Path

MAXX_C_DIR = Path(r"C:\Users\User\Repos\Tools\Maxx_C")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

_orig_popen = subprocess.Popen


def hacer_visible_chromium(pid_objetivo: int | None = None) -> None:
    """Fuerza que la ventana de Chromium (puerto 9222) sea visible y venga al frente."""
    if sys.platform != "win32":
        return
    user32 = ctypes.windll.user32
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    for _ in range(12):
        mostradas = []

        def _cb(hwnd: int, _lparam: int) -> bool:
            buf_cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, buf_cls, 256)
            if buf_cls.value == "Chrome_WidgetWin_1":
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                buf_title = ctypes.create_unicode_buffer(512)
                user32.GetWindowTextW(hwnd, buf_title, 512)
                title = buf_title.value
                vis = bool(user32.IsWindowVisible(hwnd))
                if title and (
                    pid_objetivo is None
                    or pid.value == pid_objetivo
                    or "Chrome for Testing" in title
                    or "Chromium" in title
                    or "Hermes" in title
                    or "about:blank" in title
                ):
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                    user32.SetForegroundWindow(hwnd)
                    mostradas.append((hwnd, pid.value, vis, title))
            return True

        user32.EnumWindows(WNDENUMPROC(_cb), 0)
        if mostradas:
            for h, p, v, t in mostradas:
                print(
                    f"[Ventana Chromium visible] hwnd={h} pid={p} era_visible={v} title={t!r}",
                    flush=True,
                )
            break
        time.sleep(0.5)


class _VisiblePopen(_orig_popen):
    def __init__(self, *args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        es_chrome = False
        if isinstance(cmd, (list, tuple)) and cmd and ("chrome" in str(cmd[0]).lower()):
            es_chrome = True
        elif isinstance(cmd, str) and "chrome" in cmd.lower():
            es_chrome = True

        if sys.platform == "win32" and es_chrome:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 3  # SW_SHOWMAXIMIZED
            kwargs["startupinfo"] = si
            kwargs["creationflags"] = 0x00000200  # CREATE_NEW_PROCESS_GROUP (sin DETACHED_PROCESS)

        super().__init__(*args, **kwargs)
        if es_chrome:
            hacer_visible_chromium(self.pid)


subprocess.Popen = _VisiblePopen  # type: ignore[misc]

if __name__ == "__main__":
    os.chdir(MAXX_C_DIR)
    sys.path.insert(0, str(MAXX_C_DIR))
    sys.path.insert(0, str(MAXX_C_DIR / "src"))

    from wpa.runner import Runner
    from scripts.camara import SONDA, matar_servicio_de_video

    _orig_run_step = Runner._run_step

    async def _patched_run_step(self: Runner, step, base_url=None):
        if getattr(step, "id", None) == 74.5:
            try:
                inv = self.page.locator("[data-testid$='photo-id-invalid-camera-icon-svg']")
                if await inv.count() > 0:
                    estado = await self.page.evaluate(SONDA)
                    if not estado.get("ok"):
                        print("  [AUTO-CAMARA] Servicio de video caido a mitad de corrida; reviviendo...", flush=True)
                        matar_servicio_de_video()
                        await self.page.evaluate(SONDA)
                    btn = self.page.locator(
                        "[data-testid^='compliance-customer-id-form-carousel-element-container-'] button"
                    ).first
                    if await btn.count() > 0 and await btn.is_visible():
                        print("  [AUTO-CAMARA] Pulsando 'Reintentar' en la tarjeta de foto...", flush=True)
                        await btn.click()
            except Exception as e:
                print(f"  [AUTO-CAMARA] Aviso: {e}", flush=True)
        return await _orig_run_step(self, step, base_url)

    Runner._run_step = _patched_run_step  # type: ignore[assignment]

    sys.argv[0] = str(MAXX_C_DIR / "wpa.py")
    runpy.run_path(str(MAXX_C_DIR / "wpa.py"), run_name="__main__")
