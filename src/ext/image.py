import pygame

def load_image(path: str, extension=".png"):
    if path is None:
        return None
    return pygame.image.load("assets/images/" + path + extension).convert_alpha()

def rotate_surface(image, angle):
    return pygame.transform.rotate(image, angle)

def scale_surface(image, size):
    return pygame.transform.scale(image, size)

def scale_surface_by(surface: pygame.Surface, factor: tuple[float, float] | float) -> pygame.Surface:
    if isinstance(factor, float) or isinstance(factor, int):
        factor = (factor, factor)

    width  = int(surface.get_width()  * factor[0])
    height = int(surface.get_height() * factor[1])
    return scale_surface(surface, (width, height))

def nine_slice_scale(image: pygame.Surface, target_size: tuple[int, int], corner: int) -> pygame.Surface:
    """Scale image to target_size using 9-slice.

    corner: size of the corner region in the SOURCE image (pixels).
    Corners are copied at their original pixel size (no distortion).
    Edges are stretched in one axis; the center fills the remaining area.
    Uses nearest-neighbour (pygame.transform.scale) to keep pixel art crisp.
    """
    src_w, src_h = image.get_size()
    dst_w, dst_h = target_size
    result = pygame.Surface(target_size, pygame.SRCALPHA)

    msx = src_w - corner * 2   # mid width  in source
    msy = src_h - corner * 2   # mid height in source
    mdx = dst_w - corner * 2   # mid width  in dest
    mdy = dst_h - corner * 2   # mid height in dest

    def _blit(sx, sy, sw, sh, dx, dy, dw, dh):
        piece = image.subsurface((sx, sy, sw, sh))
        if (sw, sh) != (dw, dh):
            piece = pygame.transform.scale(piece, (dw, dh))
        result.blit(piece, (dx, dy))

    c = corner
    sw, sh = src_w, src_h
    dw, dh = dst_w, dst_h

    # corners (no scaling)
    _blit(0,      0,      c, c,  0,      0,      c, c)
    _blit(sw - c, 0,      c, c,  dw - c, 0,      c, c)
    _blit(0,      sh - c, c, c,  0,      dh - c, c, c)
    _blit(sw - c, sh - c, c, c,  dw - c, dh - c, c, c)
    # edges (stretch in one axis)
    _blit(c, 0,      msx, c,   c, 0,      mdx, c)
    _blit(c, sh - c, msx, c,   c, dh - c, mdx, c)
    _blit(0,      c, c, msy,   0,      c, c, mdy)
    _blit(sw - c, c, c, msy,   dw - c, c, c, mdy)
    # center (stretch in both axes)
    _blit(c, c, msx, msy,  c, c, mdx, mdy)

    return result
