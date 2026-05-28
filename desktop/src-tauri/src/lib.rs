//! DevPulse Desktop — Tauri 应用入口
//!
//! 启动时自动拉起 Python 后端服务（FastAPI :8000），关闭时自动终止。
//! 系统托盘图标 + 右键菜单（显示窗口/退出）。

use std::io::Write;
use std::os::windows::process::CommandExt;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};

/// Windows CREATE_NO_WINDOW flag — 子进程不弹出控制台窗口
const CREATE_NO_WINDOW: u32 = 0x08000000;

/// 后端进程句柄，用于应用关闭时清理
struct BackendProcess(Mutex<Option<Child>>);

/// 后端 Python 项目路径
const BACKEND_DIR: &str = r"E:\Github Project\DevPulse\backend";

fn log(msg: &str) {
    let log_path = format!(r"{}\devpulse_tauri.log", BACKEND_DIR);
    if let Ok(mut f) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_path)
    {
        let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");
        let _ = writeln!(f, "[{}] {}", ts, msg);
        let _ = f.flush();
    }
}

/// 启动 Python 后端服务并等待它就绪
fn start_backend() -> Option<Child> {
    let python = format!(r"{}\venv\Scripts\python.exe", BACKEND_DIR);

    log(&format!(
        "Attempting to start backend: {} in {}",
        python, BACKEND_DIR
    ));

    // 方案1：直接 spawn Python（首选方式）
    let child = Command::new(&python)
        .args([
            "-m",
            "uvicorn",
            "devpulse.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--log-level",
            "warning",
        ])
        .current_dir(BACKEND_DIR)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .creation_flags(CREATE_NO_WINDOW)
        .spawn();

    match child {
        Ok(child) => {
            let pid = child.id();
            log(&format!("Backend spawned with PID: {}", pid));

            // 等待后端就绪（最多 15 秒）
            let max_retries = 30;
            for i in 0..max_retries {
                std::thread::sleep(Duration::from_millis(500));
                // 通过 TCP 连接检测 8000 端口是否就绪
                if std::net::TcpStream::connect_timeout(
                    &"127.0.0.1:8000"
                        .parse()
                        .expect("hardcoded address"),
                    Duration::from_secs(1),
                )
                .is_ok()
                {
                    log(&format!("Backend ready after {}ms", (i + 1) * 500));
                    return Some(child);
                }
            }
            log("Backend spawn succeeded but failed to become ready within timeout");
            return Some(child);
        }
        Err(e) => {
            log(&format!(
                "Direct spawn failed: {} (python path: {})",
                e, python
            ));
        }
    }

    // 方案2：用 cmd /c 包装（预防某些 Windows 环境问题）
    let cmd_args = format!(
        r#""{}" -m uvicorn devpulse.main:app --host 127.0.0.1 --port 8000 --log-level warning"#,
        python
    );
    log("Trying cmd fallback...");

    match Command::new("cmd")
        .args(["/c", &cmd_args])
        .current_dir(BACKEND_DIR)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .creation_flags(CREATE_NO_WINDOW)
        .spawn()
    {
        Ok(child) => {
            let pid = child.id();
            log(&format!("Backend spawned via cmd with PID: {}", pid));

            for i in 0..30 {
                std::thread::sleep(Duration::from_millis(500));
                if std::net::TcpStream::connect_timeout(
                    &"127.0.0.1:8000"
                        .parse()
                        .expect("hardcoded address"),
                    Duration::from_secs(1),
                )
                .is_ok()
                {
                    log(&format!("Backend (cmd) ready after {}ms", (i + 1) * 500));
                    return Some(child);
                }
            }
            log("Backend (cmd) not ready within timeout");
            return Some(child);
        }
        Err(e) => {
            log(&format!("cmd spawn also failed: {}", e));
        }
    }

    log("FATAL: All backend spawn attempts failed");
    None
}

/// Tauri 命令：显示窗口（供托盘菜单调用）
#[tauri::command]
fn show_window(app_handle: tauri::AppHandle) {
    if let Some(window) = app_handle.get_webview_window("main") {
        let _ = window.show();
        let _ = window.set_focus();
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .invoke_handler(tauri::generate_handler![show_window])
        .setup(|app| {
            log("Tauri setup started");

            // 启动后端
            let child = start_backend();
            app.manage(BackendProcess(Mutex::new(child)));

            // ── 构建系统托盘 ─────────────────────────
            let show_item = MenuItemBuilder::with_id("show", "显示窗口")
                .accelerator("Ctrl+Shift+D")
                .build(app)?;
            let quit_item = MenuItemBuilder::with_id("quit", "退出")
                .accelerator("Ctrl+Q")
                .build(app)?;

            let menu = MenuBuilder::new(app)
                .item(&show_item)
                .separator()
                .item(&quit_item)
                .build()?;

            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("DevPulse - AI 潮汐")
                .menu(&menu)
                .on_tray_icon_event(|tray_handle, event| {
                    // 左键点击显示窗口
                    if matches!(
                        event,
                        TrayIconEvent::Click {
                            button: MouseButton::Left,
                            button_state: MouseButtonState::Up,
                            ..
                        }
                    ) {
                        let app = tray_handle.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .on_menu_event(|app_handle, event| match event.id().as_ref() {
                    "show" => {
                        if let Some(window) = app_handle.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "quit" => {
                        // 清理后端进程
                        let state = app_handle.state::<BackendProcess>();
                        if let Ok(mut guard) = state.0.lock() {
                            if let Some(ref mut child) = *guard {
                                let _ = child.kill();
                                log("Backend stopped on tray quit");
                            }
                        }
                        app_handle.exit(0);
                    }
                    _ => {}
                })
                .build(app)?;

            log("Tray icon built successfully");
            log("Tauri setup complete");
            Ok(())
        })
        .on_window_event(|window, event| {
            use tauri::WindowEvent;

            match event {
                // 关闭按钮 → 隐藏到托盘（不退出）
                WindowEvent::CloseRequested { api, .. } => {
                    api.prevent_close();
                    let _ = window.hide();
                    log("Window hidden to tray (close prevented)");
                }
                // 窗口真正销毁时才清理后端
                WindowEvent::Destroyed => {
                    let state = window.state::<BackendProcess>();
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(ref mut child) = *guard {
                            let _ = child.kill();
                            log("Backend stopped on window destroy");
                        }
                    };
                }
                _ => {}
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
