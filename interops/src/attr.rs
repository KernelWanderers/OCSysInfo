use cpython::{ToPyObject, Python, PyObject, PyDict, PythonObject};
use crossterm::event::KeyCode;
use crossterm::event::KeyModifiers;

///
/// An enum to hold acceptable keycode values
/// when capturing key presses.
/// 
/// Valid keycodes:
/// * `CONTROL` => Control + C
/// * `DOWN`    => Down arrow
/// * `ENTER`   => Enter key
/// * `ESC`     => Escape key
/// * `EXIT`    => Custom definition; Control + C
/// * `LEFT`    => Left arrow / ESC key
/// * `RIGHT`   => Right arrow / Enter key
/// * `UP`      => Up arrow
#[derive(Debug)]
pub enum ValidKeyCodes {
    KeyCode(KeyCode),
    KeyModifiers(KeyModifiers)
}

#[derive(Debug)]
pub struct KeyCapture {
    pub modifier: String,
    pub keycode: String
}

impl ToPyObject for KeyCapture {
    type ObjectType = PyObject;

    fn to_py_object(&self, py: Python) -> PyObject {
        let dict = PyDict::new(py);

        dict.set_item(py, "key", self.keycode.clone()).unwrap();
        dict.set_item(py, "modifier", self.modifier.clone()).unwrap();

        dict.into_object()
    }
}

impl ValidKeyCodes {
    pub fn from_val(val: ValidKeyCodes) -> String {
        match val {
            ValidKeyCodes::KeyCode(key) => {
                match key {
                    KeyCode::Down        => "DOWN".to_string(),
                    KeyCode::Enter |
                    KeyCode::Right       => "ENTER".to_string(),
                    KeyCode::Esc   |
                    KeyCode::Left        => "ESC".to_string(),
                    KeyCode::Up          => "UP".to_string(),
                    KeyCode::Char(c)     => c.to_string(),
                    _                    => "UNKNOWN".to_string()
                }},

            ValidKeyCodes::KeyModifiers(key_mod) => 
                match key_mod {
                    KeyModifiers::CONTROL   => "CONTROL".to_string(),
                    _                       => "UNKNOWN".to_string()
                },
        }
    }
}