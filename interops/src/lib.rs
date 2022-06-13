// Relative imports
mod attr;

// Imports from crates and modules
use attr::{KeyCapture, ValidKeyCodes};
use cpython::{PyResult, Python, py_module_initializer, py_fn};
use crossterm::event;
use crossterm::event::{poll, Event, KeyCode, KeyModifiers};
use crossterm::terminal;
use std::io::stdout;
use std::io::Write;
use std::time::Duration;

// Add bindings for python
//
// Credits to vzwGrey (https://github.com/vzwGrey)
// for helping me implement Rust bindings
// into the Python portion of this codebase.
py_module_initializer!(interops, |py, m| {
    m.add(py, "__doc__", "Captures a key presse and binds this library to Python from Rust.")?;
    m.add(py, "capture_key", py_fn!(py, capture_key_py()))?;
    Ok(())
});

pub fn capture_key() -> KeyCapture {
    terminal::enable_raw_mode().unwrap();
    stdout().flush().unwrap();

    let mut modifier: String = String::new();
    let mut keycapt: String = String::new();
    let mut data = KeyCapture {
        keycode: String::new(),
        modifier: String::new(),
    };

    while modifier.len() < 1 && keycapt.len() < 1 {
        if poll(Duration::from_millis(100)).ok().unwrap() {
            if let Event::Key(key) = event::read().ok().unwrap() {
                if key.modifiers != KeyModifiers::NONE {
                    modifier = ValidKeyCodes::from_val(ValidKeyCodes::KeyModifiers(key.modifiers));
                }
                
                if key.code != KeyCode::Null {
                    keycapt = ValidKeyCodes::from_val(ValidKeyCodes::KeyCode(key.code));
                }
                
                data = KeyCapture {
                    keycode: keycapt.clone(),
                    modifier: modifier.clone(),
                };
            } else {
                continue;
            }
        } else {
            continue;
        }
    }
    
    terminal::disable_raw_mode().unwrap();

    data
}

pub fn capture_key_py(_: Python) -> PyResult<KeyCapture> {
    Ok(capture_key())
}