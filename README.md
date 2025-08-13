# chaino — Python Host Library for Chaino Devices

'chaino' module lets a PC communicate with an Arduino/compatible board that runs the Chaino firmware over **Serial (USB)**. You can remotely execute functions registered on the board, pass arguments, and receive return values. It uses **CRC-16/XMODEM** for integrity and includes resend/retry logic.

---

## 📦 Requirements & Installation

- Python 3.8+
- [pyserial](https://pypi.org/project/pyserial/)

```bash
pip install pyserial
