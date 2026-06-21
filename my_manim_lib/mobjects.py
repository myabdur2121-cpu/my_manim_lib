# paste your Mobject classes here
from manim import *
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial.distance import cdist
from scipy.ndimage import gaussian_filter


class GlowLine(VGroup):
    def __init__(
        self,
        start=LEFT * 3,
        end=RIGHT * 3,
        color=ORANGE,
        max_radius=1.5,         # গাণিতিক ব্যাসার্ধ (GlowDot এর সাথে মিল রাখার জন্য)
        max_stroke_width=60,    # লাইনের সর্বোচ্চ পুরুত্ব (ম্যানিমে গ্লো ইফেক্টের জন্য)
        num_layers=40,          # লেয়ার সংখ্যা
        sigma=0.5,              # সিগমা ভ্যালু
        glow_opacity=0.15,      # সর্বোচ্চ অপাসিটি স্কেল
        dist_func=None,         # ইকুয়েশন চেঞ্জ করার প্যারামিটার
        **kwargs
    ):
        super().__init__(**kwargs)

        # ডিফল্ট হিসেবে গ্রাশিয়ান (Gaussian) ডিস্ট্রিবিউশন সমীকরণ
        if dist_func is None:
            self.dist_func = lambda r, s, max_r: np.exp(-(r**2) / (2 * (s**2)))
        else:
            self.dist_func = dist_func

        # GlowDot-এর মতো হুবহু একই উল্টো লুপ (বড় থেকে ছোট লেয়ার)
        for i in range(num_layers, 0, -1):
            # গাণিতিক দূরত্ব (r) হিসাব
            r = (i / num_layers) * max_radius

            # আপনার সেই কাস্টম বা ডিফল্ট ইকুয়েশন দিয়ে অপাসিটি বের করা
            opacity = self.dist_func(r, sigma, max_radius)
            opacity = np.clip(opacity, 0, 1)

            # গাণিতিক ব্যাসার্ধকে (r) লাইনের স্ট্রোক উইডথ-এ রূপান্তর
            current_stroke_width = (r / max_radius) * max_stroke_width

            # বৃত্তের পরিবর্তে এখানে Line অবজেক্ট লেয়ারিং হচ্ছে
            layer = Line(
                start=start,
                end=end,
                stroke_width=current_stroke_width,
                color=color,
                stroke_opacity=opacity * glow_opacity
            )
            self.add(layer)


class GlowDot(VGroup):
    def __init__(
        self,
        color=ORANGE,
        max_radius=1.5,
        num_layers=40,
        sigma=0.5,
        glow_opacity=0.15,
        dist_func=None,
        **kwargs
    ):
        super().__init__(**kwargs)

        if dist_func is None:
            # ডিফল্ট গাউসিয়ান ডিস্ট্রিবিউশন
            self.dist_func = lambda r, s, max_r: np.exp(-(r**2) / (2 * (s**2)))
        else:
            self.dist_func = dist_func

        for i in range(num_layers, 0, -1):
            r = (i / num_layers) * max_radius
            opacity = self.dist_func(r, sigma, max_radius)
            opacity = np.clip(opacity, 0, 1)

            layer = Circle(
                radius=r,
                stroke_width=0,
                fill_color=color,
                fill_opacity=opacity * glow_opacity
            )
            self.add(layer)


class Glow(VGroup):
    def __init__(
        self,
        mobject,                  # ইনপুট হিসেবে যেকোনো VMobject (Circle, Square, Triangle ইত্যাদি)
        color=None,               # গ্লো এর কালার (None থাকলে অবজেক্টের নিজের কালারটাই নেবে)
        max_radius=1.5,           # গাণিতিক ব্যাসার্ধ
        max_stroke_width=60,      # সর্বোচ্চ আলোর পুরুত্ব
        num_layers=40,            # লেয়ার সংখ্যা
        sigma=0.5,                # সিগমা (আলোর ছড়ানো নিয়ন্ত্রণকারী)
        glow_opacity=0.15,        # আলোর মূল তীব্রতা বা ভোল্টেজ
        dist_func=None,           # কাস্টম ইকুয়েশন প্যারামিটার (ডিফল্ট গাউসিয়ান)
        overlay_original=True,    # আপনার চাওয়া সেই বুলিয়ান প্যারামিটার (True/False)
        **kwargs
    ):
        super().__init__(**kwargs)

        # যদি আলাদা রঙ না দেওয়া হয়, তবে ইনপুট অবজেক্টের রঙটাই গ্লো এর রঙ হবে
        glow_color = color if color is not None else mobject.get_color()

        # ডিফল্ট গাউসিয়ান ইকুয়েশন
        if dist_func is None:
            self.dist_func = lambda r, s, max_r: np.exp(-(r**2) / (2 * (s**2)))
        else:
            self.dist_func = dist_func

        # গ্লো লেয়ারিং লুপ (বাহির থেকে ভেতরে)
        for i in range(num_layers, 0, -1):
            r = (i / num_layers) * max_radius
            opacity = self.dist_func(r, sigma, max_radius)
            opacity = np.clip(opacity, 0, 1)

            current_stroke_width = (r / max_radius) * max_stroke_width

            # মেশিন ট্রিক: ইনপুট অবজেক্টের একটি করে কপি বানিয়ে বর্ডারে গ্লো দেওয়া হচ্ছে
            layer = mobject.copy()
            layer.set_fill(opacity=0)  # গ্লো লেয়ারের পেটের ভেতর ফাঁপা থাকবে, শুধু বাহু থেকে আলো জ্বলবে
            layer.set_stroke(
                color=glow_color,
                width=current_stroke_width,
                opacity=opacity * glow_opacity
            )
            self.add(layer)

        # আপনার স্পেশাল লজিক: ট্রু হলে অরিজিনাল সলিড অবজেক্টটি গ্লো-এর ওপর ওভারল্যাপ হবে
        if overlay_original:
            self.add(mobject)


class SmoothCross(VGroup):
    def __init__(
        self,
        mobject,
        min_width=2,
        max_width=6,
        max_stroke=1.0,
        max_opacity=1.0,
        color=RED,
        num_segments=80,
        **kwargs
    ):
        # Safely extract 'opacity' if passed in kwargs, default to 1.0
        base_opacity = kwargs.pop("opacity", 1.0)

        super().__init__(**kwargs)

        # FIX: Get the exact 3D corner coordinates directly using Manim's built-in directions
        ur = mobject.get_corner(UR)
        dl = mobject.get_corner(DL)
        ul = mobject.get_corner(UL)
        dr = mobject.get_corner(DR)

        # Strict sequential drawing order: UR->DL first, then UL->DR
        diagonals = [(ur, dl), (ul, dr)]

        for start, end in diagonals:
            for i in range(num_segments):
                t1 = i / num_segments
                t2 = (i + 1) / num_segments

                p1 = start + (end - start) * t1
                p2 = start + (end - start) * t2

                # Sine curve factor (0.0 at corners, 1.0 in the middle)
                progress = i / (num_segments - 1)
                sine_factor = np.sin(np.pi * progress)

                # Apply max_stroke multiplier to the width formula
                current_width = (min_width + (max_width - min_width) * sine_factor) * max_stroke

                # Smooth opacity blend
                opacity_curve = 0.4 + 0.6 * sine_factor
                current_opacity = base_opacity * max_opacity * opacity_curve

                segment = Line(
                    p1, p2,
                    stroke_width=current_width,
                    stroke_opacity=current_opacity,
                    color=color
                )
                self.add(segment)


class BrightGlowDot(ImageMobject):
    def __init__(self,
                 resolution=100,
                 glow_colors=['#0000FF'],
                 bright_core=True,
                 core_colors=['#FFFFFF'],
                 opacity_equation=None,
                 **kwargs):
        """
        Manim CE Custom GlowDot
        -----------------------
        resolution : গ্রিডের সাইজ (১০০ দিলে ১০০x১০০ = ১০,০০০ বক্স হবে)
        glow_colors : গ্লো-এর মূল রঙ (যেমন: ব্লু)
        bright_core : কেন্দ্রে মিক্সড লাইট এফেক্ট থাকবে কিনা (True/False)
        core_colors : কেন্দ্রের ভেতরের রঙ (ডিফল্ট: হোয়াইট)
        opacity_equation : ওপাসিটি পরিবর্তনের কাস্টম গাণিতিক ইকুয়েশন
        """
        self.resolution = resolution
        self.glow_colors = glow_colors
        self.bright_core = bright_core
        self.core_colors = core_colors

        # ডিফল্ট ইকুয়েশন: কেন্দ্র থেকে দূরে গেলে ওপাসিটি মসৃণভাবে কমবে
        if opacity_equation is None:
            self.opacity_equation = lambda d: np.exp(-5 * (d ** 2))
        else:
            self.opacity_equation = opacity_equation

        # ইমেজ ডেটা তৈরি করা
        pixel_array = self._generate_glow_matrix()

        # Manim-এর ImageMobject-কে কল করা
        super().__init__(pixel_array, **kwargs)

    def _generate_glow_matrix(self):
        # -1 থেকে 1 পর্যন্ত কোঅর্ডিনেট গ্রিড তৈরি
        x = np.linspace(-1, 1, self.resolution)
        y = np.linspace(-1, 1, self.resolution)
        X, Y = np.meshgrid(x, y)

        # কেন্দ্র (Axis Origin) থেকে দূরত্ব হিসাব
        distance = np.sqrt(X**2 + Y**2)
        distance = np.clip(distance, 0, 1)

        # ১. ওপাসিটি ইকুয়েশন অ্যাপ্লাই (০ থেকে ২৫৫ স্কেলে)
        opacity_matrix = (self.opacity_equation(distance) * 255).astype(np.uint8)

        # ২. কালার ব্লেন্ডিং (কোর কালার + গ্লো কালার মিক্সিং)
        final_colors = []
        if self.bright_core:
            final_colors.extend(self.core_colors)
        final_colors.extend(self.glow_colors)

        cmap = LinearSegmentedColormap.from_list("glow_gradient", final_colors)
        rgb_matrix = (cmap(distance)[:, :, :3] * 255).astype(np.uint8)

        # ৩. RGBA (Red, Green, Blue, Alpha) ম্যাট্রিক্স তৈরি
        rgba_matrix = np.zeros((self.resolution, self.resolution, 4), dtype=np.uint8)
        rgba_matrix[:, :, :3] = rgb_matrix
        rgba_matrix[:, :, 3] = opacity_matrix

        return rgba_matrix


class MultiBrightGlow(Group):
    def __init__(self,
                 vmobjects,
                 exclude_indices=None,
                 mode="combined",
                 resolution=150,
                 glow_range=0.5,
                 glow_colors=['#0000FF'],
                 bright_core=True,
                 core_colors=['#FFFFFF'],
                 opacity_equation=None,
                 VMob_overlay=True,
                 **kwargs):

        super().__init__(**kwargs)

        if isinstance(vmobjects, (list, tuple)):
            self.vmobjects = list(vmobjects)
        elif isinstance(vmobjects, (MathTex, Tex, Text)):
            self.vmobjects = [vmobjects]
        elif isinstance(vmobjects, (VGroup, Group)):
            self.vmobjects = list(vmobjects)
        else:
            self.vmobjects = [vmobjects]

        self.exclude_indices = exclude_indices if exclude_indices is not None else []
        self.mode = mode.lower()
        self.resolution = resolution
        self.glow_range = glow_range

        # কালার অটো-র‍্যাপিং ফিক্স: লিস্ট না দিলে স্বয়ংক্রিয়ভাবে লিস্টে রূপান্তর করবে
        if isinstance(glow_colors, (list, tuple, np.ndarray)):
            self.glow_colors = list(glow_colors)
        else:
            self.glow_colors = [glow_colors]

        if isinstance(core_colors, (list, tuple, np.ndarray)):
            self.core_colors = list(core_colors)
        else:
            self.core_colors = [core_colors]

        self.bright_core = bright_core
        self.VMob_overlay = VMob_overlay

        if opacity_equation is None:
            self.opacity_equation = lambda d: np.exp(-4 * (d / self.glow_range) ** 2)
        else:
            self.opacity_equation = opacity_equation

        glow_image = self._generate_multi_glow()
        self.add(glow_image)

        if self.VMob_overlay:
            for mob in self.vmobjects:
                self.add(mob)

    def _generate_multi_glow(self):
        initial_mobs = [
            mob for i, mob in enumerate(self.vmobjects)
            if i not in self.exclude_indices
        ]

        active_mobs = []
        for mob in initial_mobs:
            for submob in mob.get_family():
                if len(submob.points) > 0 and len(submob.submobjects) == 0:
                    active_mobs.append(submob)

        if not active_mobs:
            return VMobject()

        num_samples = 1000

        if self.mode == "union" and len(active_mobs) > 1:
            target_mob = Union(*active_mobs)
            shape_pts = np.array([target_mob.point_from_proportion(t)[:2] for t in np.linspace(0, 1, num_samples)])
        elif self.mode == "intersection" and len(active_mobs) > 1:
            target_mob = Intersection(*active_mobs)
            shape_pts = np.array([target_mob.point_from_proportion(t)[:2] for t in np.linspace(0, 1, num_samples)])
        else:
            all_pts = []
            pts_per_mob = max(20, num_samples // len(active_mobs))
            for mob in active_mobs:
                pts = [mob.point_from_proportion(t)[:2] for t in np.linspace(0, 1, pts_per_mob)]
                all_pts.extend(pts)
            shape_pts = np.array(all_pts)

        padding = self.glow_range
        min_x, max_x = np.min(shape_pts[:, 0]) - padding, np.max(shape_pts[:, 0]) + padding
        min_y, max_y = np.min(shape_pts[:, 1]) - padding, np.max(shape_pts[:, 1]) + padding

        x = np.linspace(min_x, max_x, self.resolution)
        y = np.linspace(max_y, min_y, self.resolution)
        X, Y = np.meshgrid(x, y)
        grid_pts = np.vstack([X.ravel(), Y.ravel()]).T

        distances = cdist(grid_pts, shape_pts).min(axis=1)
        distance_matrix = distances.reshape(self.resolution, self.resolution)

        norm_dist = np.clip(distance_matrix / self.glow_range, 0, 1)
        opacity_matrix = (self.opacity_equation(distance_matrix) * 255).astype(np.uint8)

        raw_colors = []
        if self.bright_core:
            raw_colors.extend(self.core_colors)
        raw_colors.extend(self.glow_colors)

        # ম্যাজিক ফিক্স ২: ManimColor অবজেক্টকে Matplotlib এর চেনা স্ট্যান্ডার্ড Hex স্ট্রিং-এ কনভার্ট করা
        cleaned_colors = []
        for c in raw_colors:
            if hasattr(c, "to_hex"):
                cleaned_colors.append(c.to_hex())
            else:
                cleaned_colors.append(str(c))

        cmap = LinearSegmentedColormap.from_list("multi_glow", cleaned_colors)
        rgb_matrix = (cmap(norm_dist)[:, :, :3] * 255).astype(np.uint8)

        rgba_matrix = np.zeros((self.resolution, self.resolution, 4), dtype=np.uint8)
        rgba_matrix[:, :, :3] = rgb_matrix
        rgba_matrix[:, :, 3] = opacity_matrix

        img = ImageMobject(rgba_matrix)
        img.stretch_to_fit_width(max_x - min_x)
        img.stretch_to_fit_height(max_y - min_y)
        img.move_to(np.array([(min_x + max_x)/2, (min_y + max_y)/2, 0]))

        return img


class ScreenBlur(ImageMobject):
    def __init__(self, scene, sigma=15, **kwargs):
        """
        হাই-লেভেল স্ক্রিন ব্লার এপিআই (রেন্ডারার আপডেট + মুভিং ক্যামেরা ফ্রেন্ডলি)
        """
        # 🛠️ ১. আপনার তথ্য অনুযায়ী: রেন্ডারারকে ফোর্স করা কারেন্ট ফ্রেমটি বেক/আপডেট করতে
        scene.renderer.update_frame(scene)

        # 🛠️ ২. আপনার তথ্য অনুযায়ী: রেন্ডারার থেকে সরাসরি কারেন্ট ফ্রেমের পিক্সেল অ্যারে নেওয়া
        screen_pixels = scene.renderer.get_frame()

        # ৩. আপনার তথ্য অনুযায়ী: ডাইনামিক সিগমা ও চ্যানেল প্রটেকশন (কালার ডিস্টরশন রোধে)
        current_height = screen_pixels.shape[0]
        dynamic_sigma = sigma * (current_height / 480.0)

        # sigma-র শেষ ভ্যালু ০ রাখা হয়েছে যাতে কালার চ্যানেলে ব্লার না হয়
        blurred_pixels = gaussian_filter(screen_pixels.astype(float), sigma=(dynamic_sigma, dynamic_sigma, 0))
        blurred_pixels = np.clip(blurred_pixels, 0, 255).astype(np.uint8)

        # ৪. পিক্সেল অ্যারে থেকে সরাসরি ImageMobject তৈরি করা
        super().__init__(blurred_pixels, **kwargs)

        # 🛠️ ৫. মুভিং ক্যামেরার বর্তমান জুম সাইজ ট্র্যাক করে ইমেজের সাইজ ফিক্স করা
        self.set_width(scene.camera.frame.get_width())
        self.set_height(scene.camera.frame.get_height())

        # 🛠️ ৬. মুভিং ক্যামেরা এই মুহূর্তে যেখানে তাকিয়ে আছে, ঠিক সেখানে ইমেজটি বসানো
        self.move_to(scene.camera.frame.get_center())


class TrueGaussianBlur2(ImageMobject):
    def __init__(self, mobject, resolution=200, sigma=8, padding=1.5, **kwargs):
        """
        অপ্টিমাইজড গসিয়ান ব্লার মেথড (NumPy জেনারেটেড পয়েন্ট ক্লাউড)
        """
        xmin, ymin, _ = mobject.get_corner(DL) - padding
        xmax, ymax, _ = mobject.get_corner(UR) + padding

        width = xmax - xmin
        height = ymax - ymin

        # গ্রিড তৈরি
        r_grid = np.zeros((resolution, resolution), dtype=float)
        g_grid = np.zeros((resolution, resolution), dtype=float)
        b_grid = np.zeros((resolution, resolution), dtype=float)
        a_grid = np.zeros((resolution, resolution), dtype=float)

        for submob in mobject.get_family():
            if hasattr(submob, "points") and len(submob.points) > 0:
                color_rgb = color_to_rgb(submob.get_color())

                # ম্যাজিক ফিক্স: ধীরগতির point_from_proportion লুপ বাদ দিয়ে
                # ম্যানিমের নিজস্ব ফাস্ট curve subdivision ব্যবহার করা হয়েছে
                try:
                    submob_dense = submob.copy()
                    submob_dense.insert_n_curves(25) # পলকের মধ্যে পুরো অবজেক্টের পয়েন্ট ঘন করবে
                    points = submob_dense.points
                except:
                    points = submob.points

                if len(points) == 0:
                    continue

                # গ্রিড ইনডেক্স ম্যাপিং
                x_indices = ((points[:, 0] - xmin) / width * (resolution - 1)).astype(int)
                y_indices = ((ymax - points[:, 1]) / height * (resolution - 1)).astype(int)

                valid = (x_indices >= 0) & (x_indices < resolution) & (y_indices >= 0) & (y_indices < resolution)
                x_indices = x_indices[valid]
                y_indices = y_indices[valid]

                r_grid[y_indices, x_indices] = color_rgb[0]
                g_grid[y_indices, x_indices] = color_rgb[1]
                b_grid[y_indices, x_indices] = color_rgb[2]
                a_grid[y_indices, x_indices] = 1.0

        # গসিয়ান ফিল্টার মেথড
        blurred_r = gaussian_filter(r_grid, sigma=sigma)
        blurred_g = gaussian_filter(g_grid, sigma=sigma)
        blurred_b = gaussian_filter(b_grid, sigma=sigma)
        blurred_a = gaussian_filter(a_grid, sigma=sigma)

        mask = blurred_a > 0.001
        final_r = np.zeros_like(blurred_r)
        final_g = np.zeros_like(blurred_g)
        final_b = np.zeros_like(blurred_b)

        final_r[mask] = blurred_r[mask] / blurred_a[mask]
        final_g[mask] = blurred_g[mask] / blurred_a[mask]
        final_b[mask] = blurred_b[mask] / blurred_a[mask]

        final_r = np.clip(final_r, 0, 1)
        final_g = np.clip(final_g, 0, 1)
        final_b = np.clip(final_b, 0, 1)

        if blurred_a.max() > 0:
            final_a = blurred_a / blurred_a.max()
        else:
            final_a = blurred_a
        final_a = np.clip(final_a, 0, 1)

        # আরজিবিএ ইমেজ ম্যাট্রিক্স
        rgba_matrix = np.zeros((resolution, resolution, 4), dtype=np.uint8)
        rgba_matrix[:, :, 0] = (final_r * 255).astype(np.uint8)
        rgba_matrix[:, :, 1] = (final_g * 255).astype(np.uint8)
        rgba_matrix[:, :, 2] = (final_b * 255).astype(np.uint8)
        rgba_matrix[:, :, 3] = (final_a * 255).astype(np.uint8)

        super().__init__(rgba_matrix, **kwargs)

        self.stretch_to_fit_width(width)
        self.stretch_to_fit_height(height)
        self.move_to(mobject.get_center())
        

class SplitTex(Tex):
    def __init__(self, text_string, *args, word_spacing=r"\ ", **kwargs):
        # Note: The input string is split into individual words using the split method.
        words = text_string.split()
        
        # Note: The LaTeX spacing character is prepended to every word after the first one.
        processed_words = [
            word if i == 0 else word_spacing + word
            for i, word in enumerate(words)
        ]
        
        # Note: All processed word arguments are unpacked into the parent Tex class.
        super().__init__(*processed_words, *args, **kwargs)

class SplitMathTex(MathTex):
    def __init__(self, math_string, *args, **kwargs):
        # Note: The math equation string is split by spaces into individual segments.
        math_parts = math_string.split()
        
        # Note: The segments are passed directly into the parent MathTex initialization.
        super().__init__(*math_parts, *args, **kwargs)
        
