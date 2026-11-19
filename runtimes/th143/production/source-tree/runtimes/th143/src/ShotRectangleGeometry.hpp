#pragma once
namespace th143 {
// Original406490 and404c10, including the circumcircle rejection and
// ordered float corner/edge tests rather than a replacement SAT formula.
bool shot_rectangle_rectangle(float x,float y,float width,float height,float angle,
                              float other_x,float other_y,float other_width,float other_height,float other_angle);
}
