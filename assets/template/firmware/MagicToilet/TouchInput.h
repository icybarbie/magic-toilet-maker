#pragma once
#include <stdint.h>
#include <stddef.h>

enum class TouchKind { None, Up, Down };
struct TouchReport { TouchKind kind; int x; int y; };

// CST9217 report format from the bundled SensorLib CST92xx driver.
// Unlike getPoint(), distinguish "no valid packet" from a real release.
inline TouchReport decodeTouch(const uint8_t *p, size_t n) {
  if (n < 7 || p[6] != 0xAB) return {TouchKind::None, 0, 0};
  unsigned count = p[5] & 0x7f;
  if (count > 2) return {TouchKind::None, 0, 0};
  if (!count || (p[4] & 0x80)) return {TouchKind::Up, 0, 0};
  if ((p[0] & 0xf) != 6) return {TouchKind::Up, 0, 0};
  if ((p[0] >> 4) >= 2) return {TouchKind::None, 0, 0};
  int x = (p[1] << 4) | (p[3] >> 4);
  int y = (p[2] << 4) | (p[3] & 0xf);
  if (x > 466 || y > 466) return {TouchKind::None, 0, 0};
  // Same two-axis mirroring as the original board example, clipped at edge.
  return {TouchKind::Down, x ? 466-x : 465, y ? 466-y : 465};
}

struct TouchLatch {
  bool down = false;
  uint32_t lastDown = 0;
  bool update(TouchReport r, uint32_t now) {
    if (r.kind == TouchKind::None) return false;
    if (r.kind == TouchKind::Up) { down = false; return false; }
    // The controller sends held-contact reports about once a second. Recover
    // if a release was lost, without repeatedly firing on a held finger.
    bool fresh = !down || uint32_t(now-lastDown) > 1500;
    down = true; lastDown = now;
    return fresh;
  }
};
