# Bluetooth-kaiuttimen asennus Ubuntulle

## 1. Parinna kaiutin

```bash
bluetoothctl
> power on
> agent on
> scan on
# Odota kunnes kaiutin näkyy listalla
> connect XX:XX:XX:XX:XX:XX
> trust XX:XX:XX:XX:XX:XX
> quit
```

## 2. Tarkista PulseAudio-sink

```bash
pactl list sinks short
# Esim: bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink
```

## 3. Aseta .env:iin

```
AUDIO_OUTPUT_SINK=bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink
```

## 4. Testaa

```bash
paplay --device=bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink /usr/share/sounds/alsa/Front_Left.wav
```

## Automaattinen yhteys käynnistyksessä

```bash
# /etc/pulse/default.pa loppuun:
load-module module-bluetooth-policy auto_switch=false
load-module module-bluetooth-discover
```

## Vianetsintä

- `pulseaudio --start` jos PA ei käynnisty
- `pactl info` tarkistaa PA-version
- `journalctl -u bluetooth` BT-lokeja
