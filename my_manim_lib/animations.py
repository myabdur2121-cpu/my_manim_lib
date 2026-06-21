# paste your Animation classes here
from manim import *
import numpy as np


class TrueSpiralInSubmobs(Animation):
    def __init__(self, mobject: Mobject, scale_factor: float = 2.5, rotations: float = 2.0, fade_in_fraction: float = 0.3, stagger_factor: float = 0.2, **kwargs) -> None:
        self.scale_factor = scale_factor
        self.rotations = rotations
        self.fade_in_fraction = fade_in_fraction
        self.stagger_factor = stagger_factor

        # Isolate individual character glyph paths safely
        self.characters = [m for m in mobject.get_family() if len(m.submobjects) == 0 and m.get_num_points() > 0]

        # Relative movement path parameters
        self.base_offset = RIGHT * 2.5 + UP * 1.5

        self.char_data = []
        for char in self.characters:
            char.save_state()
            final_pos = char.get_center()
            initial_pos = final_pos + self.base_offset * self.scale_factor

            self.char_data.append({
                "char": char,
                "initial_pos": initial_pos,
                "final_pos": final_pos,
                "max_fill": char.get_fill_opacity(),
                "max_stroke": char.get_stroke_opacity()
            })

        super().__init__(mobject, introducer=True, **kwargs)

    def interpolate_mobject(self, alpha: float) -> None:
        num_chars = len(self.char_data)

        for i, data in enumerate(self.char_data):
            char = data["char"]
            char.restore()

            if num_chars > 1:
                start_delay = (i / (num_chars - 1)) * self.stagger_factor
            else:
                start_delay = 0

            if alpha < start_delay:
                local_alpha = 0.0
            else:
                local_alpha = (alpha - start_delay) / (1.0 - start_delay)

            alpha_f = self.rate_func(local_alpha)

            vec = data["initial_pos"] - data["final_pos"]
            dist_factor = 1.0 - alpha_f
            angle = self.rotations * TAU * (1.0 - alpha_f)

            cos_a = np.cos(angle)
            sin_a = np.sin(angle)

            rot_x = vec[0] * cos_a - vec[1] * sin_a
            rot_y = vec[0] * sin_a + vec[1] * cos_a

            current_pos = data["final_pos"] + np.array([rot_x, rot_y, 0]) * dist_factor

            char.move_to(current_pos)
            char.rotate(angle)

            fade_scale = min(1.0, alpha_f / self.fade_in_fraction)
            char.set_fill(opacity=data["max_fill"] * fade_scale)
            char.set_stroke(opacity=data["max_stroke"] * fade_scale)


class ParticleDissolve(Animation):
    """
    Animate a Mobject by breaking it into thousands of tiny particles
    that explode outward uniformly and fade away into a beautiful cloud.
    """
    def __init__(self, mobject, num_particles=1500, max_speed=5.5, **kwargs):
        self.num_particles = num_particles
        self.max_speed = max_speed
        super().__init__(mobject, **kwargs)

    def begin(self):
        all_points = []
        all_colors = []
        self.fade_targets = self.mobject.get_family()

        for submob in self.fade_targets:
            if len(submob.points) > 0:
                sub_points = submob.get_all_points()
                color = submob.get_color() if hasattr(submob, "get_color") else WHITE
                all_points.extend(sub_points)
                all_colors.extend([color] * len(sub_points))

        if len(all_points) == 0:
            all_points = [self.mobject.get_center()]
            all_colors = [self.mobject.get_color() if hasattr(self.mobject, "get_color") else WHITE]

        all_points = np.array(all_points)

        indices = np.random.choice(len(all_points), self.num_particles, replace=True)
        self.initial_positions = all_points[indices]

        self.particles = VGroup(*[
            Dot(point=self.initial_positions[i], radius=0.025, color=all_colors[indices[i]])
            for i in range(self.num_particles)
        ])

        # Mathematical Uniform Spatial Density Distribution (360 degrees)
        # Prevents hollow ring effect and ensures a perfectly filled scatter cloud
        angles = np.random.uniform(0, 2 * np.pi, self.num_particles)
        speeds = np.sqrt(np.random.uniform(0.05, 1.0, self.num_particles)) * self.max_speed

        self.velocities = np.zeros((self.num_particles, 3))
        self.velocities[:, 0] = np.cos(angles) * speeds
        self.velocities[:, 1] = np.sin(angles) * speeds

        self.mobject.add(self.particles)
        super().begin()

    def interpolate_mobject(self, alpha):
        # Fade out the original mobject early (first 25% of runtime)
        for submob in self.fade_targets:
            submob.set_opacity(max(0, 1 - alpha * 4))

        # Move particles outward uniformly
        for i, particle in enumerate(self.particles):
            new_pos = self.initial_positions[i] + self.velocities[i] * alpha
            particle.move_to(new_pos)
            particle.set_opacity(1 - alpha)

    def clean_up_from_scene(self, scene):
        self.mobject.remove(self.particles)
        scene.remove(self.mobject)
        super().clean_up_from_scene(scene)


class FlyIntoPlaceholder(AnimationGroup):
    def __init__(
        self,
        source,
        target,
        placeholder,
        run_time=2.0,
        rate_func=smooth,
        path_arc=-0.6,
        keep_source=False,
        **kwargs
    ):
        # FIX: Automatically match the exact size of the placeholder
        # This solves the "Scale Trap" completely!
        target.match_height(placeholder)

        # Now safely move it to the correct coordinate baseline
        target.move_to(placeholder)

        animation_source = source.copy() if keep_source else source

        transform_animation = FadeTransform(
            animation_source,
            target,
            path_arc=path_arc,
            run_time=run_time,
            rate_func=rate_func
        )

        super().__init__(transform_animation, **kwargs)


class SnappyPopIn(Animation):
    """
    Shorts-এর জন্য তৈরি পাঞ্চি পপ-ইন অ্যানিমেশন।
    এটি প্রতিটি অক্ষরকে তার নিজস্ব পজিশন থেকে একটি চমৎকার বাউন্স ইফেক্ট দিয়ে স্ক্রিনে নিয়ে আসে।
    """
    def __init__(self, mobject, stagger_factor=0.12, fade_fraction=0.15, **kwargs):
        self.stagger_factor = stagger_factor
        self.fade_fraction = fade_fraction

        # প্রতিটি ক্যারেক্টারকে আলাদাভাবে ট্র্যাক করা
        self.characters = [m for m in mobject.get_family() if len(m.submobjects) == 0 and m.get_num_points() > 0]

        for char in self.characters:
            char.save_state()

        super().__init__(mobject, introducer=True, **kwargs)

    def interpolate_mobject(self, alpha):
        num_chars = len(self.characters)

        # easeOutBack ম্যাথমেটিক্যাল বাউন্স ফর্মুলা (মোশন গ্রাফিক্স স্ট্যান্ডার্ড)
        c1 = 1.70158
        c3 = c1 + 1

        for i, char in enumerate(self.characters):
            char.restore()

            # ক্যারেক্টারগুলোর মাঝে সামান্য সময়ের গ্যাপ (Stagger) তৈরি করা
            if num_chars > 1:
                start_delay = (i / (num_chars - 1)) * self.stagger_factor
            else:
                start_delay = 0

            if alpha < start_delay:
                local_alpha = 0.0
            else:
                local_alpha = (alpha - start_delay) / (1.0 - start_delay)

            if local_alpha <= 0:
                char.set_opacity(0)
                continue

            # বাউন্স কার্ভ ক্যালকুলেশন
            t = local_alpha - 1
            bounce_factor = 1 + c3 * (t ** 3) + c1 * (t ** 2)

            # ক্যারেক্টারটিকে তার নিজস্ব সেন্টারের সাপেক্ষে স্কেল করা
            char.scale(max(0, bounce_factor), about_point=char.get_center())

            # দ্রুত ফেইড ইন করা
            fade_scale = min(1.0, local_alpha / self.fade_fraction)
            char.set_opacity(char.get_fill_opacity() * fade_scale)


class VectorFieldWarp(Animation):
    def __init__(self, mobject, grid, warp_intensity=1.5, **kwargs):
        self.grid = grid
        self.warp_intensity = warp_intensity

        # আদি অবস্থার ব্যাকআপ রাখা
        self.grid_original = grid.copy()
        self.mobj_original = mobject.copy()

        super().__init__(VGroup(mobject, grid), **kwargs)

    def interpolate_mobject(self, alpha):
        # সাইন ওয়েভ এনভেলপ: 0 -> 1 -> 0 (শুরু ও শেষে গ্রিড স্বাভাবিক থাকবে)
        envelope = np.sin(np.pi * alpha)

        def apply_warp(mob, orig_mob, is_mobj=False):
            mob.points = orig_mob.points.copy()

            # প্রতিটি পয়েন্টে ভোর্টেক্স বা টুইস্ট অ্যাপ্লাই করা
            for i in range(len(mob.points)):
                x, y, z = mob.points[i]
                r = np.sqrt(x**2 + y**2)
                theta = np.arctan2(y, x)

                # এক্সপোনেনশিয়াল ডিকে (কেন্দ্রের দিকে বেশি ঘুরবে)
                twist = self.warp_intensity * envelope * np.exp(-0.2 * r)

                mob.points[i, 0] = r * np.cos(theta + twist)
                mob.points[i, 1] = r * np.sin(theta + twist)

            if is_mobj:
                # অবজেক্টটি ঘূর্ণির ভেতর থেকে বড় হয়ে স্ক্রিনে আসবে
                mob.set_opacity(alpha)
                scale_factor = max(alpha, 0.001)
                mob.scale(scale_factor, about_point=ORIGIN)

        # গ্রিড এবং অবজেক্টের ওপর ফাংশন প্রয়োগ
        apply_warp(self.grid, self.grid_original, is_mobj=False)
        apply_warp(self.mobject, self.mobj_original, is_mobj=True)


class ElasticSnapIn(Animation):
    def __init__(self, mobject, damping=4.5, frequency=14.0, snap_center=None, **kwargs):
        self.damping = damping
        self.frequency = frequency

        # অবজেক্টের ভেতরের সব সাব-মবজেক্টের পয়েন্টগুলোর কপি রাখা
        self.mobject_family = mobject.family_members_with_points()
        self.orig_points = [mob.points.copy() for mob in self.mobject_family]

        # স্ন্যাপটি কোন বিন্দুকে কেন্দ্র করে হবে (ডিফল্ট: অবজেক্টের নিজস্ব কেন্দ্র)
        if snap_center is None:
            self.snap_center = mobject.get_center()
        else:
            self.snap_center = snap_center
                # --- Add this line right before super().__init__ ---
        self.orig_opacities = [(m.get_fill_opacity(), m.get_stroke_opacity()) for m in self.mobject_family]

        super().__init__(mobject, introducer=True, **kwargs)

    def interpolate_mobject(self, alpha):
        if len(self.orig_points) == 0:
            return

        # বাউন্ডারি-কারেক্টেড আন্ডারড্যাম্পড অসিলেশন ফর্মুলা
        factor = 1 - (1 - alpha) * np.exp(-self.damping * alpha) * np.cos(self.frequency * alpha)

        # প্রথম ২০% সময়ের মধ্যে অপাসিটি ০ থেকে ১ এ স্মুথলি ফেইড হবে
        opacity = min(alpha / 0.2, 1.0)
        self.mobject.set_opacity(opacity)

        # প্রতিটি বিন্দুর ওপর স্প্রিং ফিজিক্স অ্যাপ্লাই করা
        for mob, orig_pts in zip(self.mobject_family, self.orig_points):
            if len(orig_pts) == 0:
                continue

            # কেন্দ্র সাপেক্ষে পয়েন্ট স্থানান্তরিত করে ফ্যাক্টর দিয়ে গুণ এবং পুনরায় ফেরত আনা
            new_pts = (orig_pts - self.snap_center) * factor + self.snap_center
            mob.points = new_pts


class VectorFieldWarpIn(Animation):
    def __init__(self, mobject, grid, amplitude=4.0, warp_center=ORIGIN, **kwargs):
        self.grid = grid
        self.amplitude = amplitude
        self.warp_center = warp_center

        # ব্যাকগ্রাউন্ড গ্রিডের সব লাইনের অরিজিনাল পয়েন্টগুলোর কপি রাখা
        self.grid_family = self.grid.family_members_with_points()
        self.orig_grid_points = [line.points.copy() for line in self.grid_family]

        # টার্গেট অবজেক্টের সব সাব-মবজেক্টের অরিজিনাল পয়েন্টগুলোর কপি রাখা
        self.mobject_family = mobject.family_members_with_points()
        self.orig_mobject_points = [mob.points.copy() for mob in self.mobject_family]

        # introducer=True এর মাধ্যমে ম্যানিম নিজে থেকেই অবজেক্টকে সিনে যুক্ত করবে
        super().__init__(mobject, introducer=True, **kwargs)

    def interpolate_mobject(self, alpha):
        # এনভেলপ লজিক: alpha=0 তে 0, alpha=0.5 এ সর্বোচ্চ (1), alpha=1 তে আবার 0
        envelope = np.sin(np.pi * alpha)

        # --- ক. ব্যাকগ্রাউন্ড গ্রিড ওয়ার্পিং (Fully Vectorized) ---
        for line, orig_points in zip(self.grid_family, self.orig_grid_points):
            if len(orig_points) == 0:
                continue
            new_points = orig_points.copy()

            # নির্দিষ্ট ওয়ার্প সেন্টারের সাপেক্ষে রিলেটিভ এক্স-ওয়াই বের করা
            x = orig_points[:, 0] - self.warp_center[0]
            y = orig_points[:, 1] - self.warp_center[1]

            r = np.sqrt(x**2 + y**2) + 1e-5
            theta = np.arctan2(y, x)

            # কেন্দ্রের দিকে টুইস্টের তীব্রতা বেশি হবে (Exponential Decay)
            twist = self.amplitude * np.exp(-0.25 * r) * envelope
            new_theta = theta + twist

            # পুনরায় কার্তেসীয় কোঅর্ডিনেটে কনভার্ট করে ব্যাক করা
            new_points[:, 0] = r * np.cos(new_theta) + self.warp_center[0]
            new_points[:, 1] = r * np.sin(new_theta) + self.warp_center[1]
            line.points = new_points

        # --- খ. অবজেক্ট এন্ট্রি ও স্পেস-ওয়ার্পিং синхронизация ---
        # শুরুতে অবজেক্টের সাইজ ছোট থাকবে এবং আস্তে আস্তে বড় হয়ে ফুটবে
        scale_fact = alpha
        self.mobject.set_opacity(alpha)

        for mob, orig_points in zip(self.mobject_family, self.orig_mobject_points):
            if len(orig_points) == 0:
                continue
            new_points = orig_points.copy()

            # প্রথম ধাপ: অবজেক্টের বিন্দুগুলোকে স্কেল ডাউন করে কেন্দ্রের দিকে নেওয়া
            x = (orig_points[:, 0] - self.warp_center[0]) * scale_fact
            y = (orig_points[:, 1] - self.warp_center[1]) * scale_fact

            r = np.sqrt(x**2 + y**2) + 1e-5
            theta = np.arctan2(y, x)

            # দ্বিতীয় ধাপ: গ্রিডের মতোই হুবহু স্পেস-টুইস্ট কোঅর্ডিনেট ট্রান্সফর্ম অ্যাপ্লাই করা
            twist = self.amplitude * np.exp(-0.25 * r) * envelope
            new_theta = theta + twist

            new_points[:, 0] = r * np.cos(new_theta) + self.warp_center[0]
            new_points[:, 1] = r * np.sin(new_theta) + self.warp_center[1]
            mob.points = new_points


class ElasticSnapInOpacity(Animation):
    def __init__(self, mobject, damping=4.5, frequency=14.0, snap_center=None, **kwargs):
        self.damping = damping
        self.frequency = frequency

        self.mobject_family = mobject.family_members_with_points()
        self.orig_points = [mob.points.copy() for mob in self.mobject_family]

        # Fix 1: Store layout design opacities before animation starts
        self.orig_opacities = []
        for mob in self.mobject_family:
            self.orig_opacities.append({
                "fill": mob.get_fill_opacity() if hasattr(mob, "get_fill_opacity") else 1.0,
                "stroke": mob.get_stroke_opacity() if hasattr(mob, "get_stroke_opacity") else 1.0
            })

        if snap_center is None:
            self.snap_center = mobject.get_center()
        else:
            self.snap_center = snap_center

        super().__init__(mobject, introducer=True, **kwargs)

    def interpolate_mobject(self, alpha):
        if len(self.orig_points) == 0:
            return

        # Underdamped oscillation formula
        factor = 1 - (1 - alpha) * np.exp(-self.damping * alpha) * np.cos(self.frequency * alpha)
        fade_scale = min(alpha / 0.2, 1.0)

        for mob, orig_pts, opac in zip(self.mobject_family, self.orig_points, self.orig_opacities):
            if len(orig_pts) == 0:
                continue  # Fix 2: Changed from 'return' to 'continue' so it doesn't break complex groups!

            # Apply spring physics bounce
            new_pts = (orig_pts - self.snap_center) * factor + self.snap_center
            mob.points = new_pts

            # Fade fill and stroke independently based on original design settings
            if hasattr(mob, "set_fill"):
                mob.set_fill(opacity=opac["fill"] * fade_scale)
            if hasattr(mob, "set_stroke"):
                mob.set_stroke(opacity=opac["stroke"] * fade_scale)


class FlySwap(AnimationGroup):
    def __init__(self, m1, m2, run_time=1.5, lag=0, arc=PI/2, **kwargs):
        # প্রথমে দুটো অবজেক্টের বর্তমান সেন্টার পজিশন ফিক্সড ভেরিয়েবলে নিয়ে নিন
        p1 = m1.get_center()
        p2 = m2.get_center()

        # এবার একে অপরের পজিশনে পাঠান (কার্ভ পাথ সহ)
        anim1 = m1.animate.move_to(p2).set_path_arc(arc).set_run_time(run_time)
        anim2 = m2.animate.move_to(p1).set_path_arc(arc).set_run_time(run_time)

        super().__init__(anim1, anim2, lag_ratio=lag, **kwargs)


class ReplaceFlyIntoPlaceholder(AnimationGroup):
    def __init__(
        self,
        source,
        target,
        placeholder,
        run_time=2.0,
        rate_func=smooth,
        path_arc=-0.6,
        keep_source=False,
        **kwargs
    ):
        # FIX: Automatically match the exact size of the placeholder
        # This solves the "Scale Trap" completely!
        target.match_height(placeholder)

        # Now safely move it to the correct coordinate baseline
        target.move_to(placeholder)

        animation_source = source.copy() if keep_source else source

        transform_animation = ReplacementTransform(
            animation_source,
            target,
            path_arc=path_arc,
            run_time=run_time,
            rate_func=rate_func
        )
        super().__init__(transform_animation, **kwargs)


class CreateWithFlash(AnimationGroup):
    def __init__(
        self,
        mobject,
        flash_color=YELLOW,
        flash_stroke_width=8,      # Controls flash thickness
        flash_stroke_opacity=1.0,  # Controls flash opacity
        path_color=WHITE,
        path_stroke_opacity=1.0,   # Controls final line opacity
        time_width=0.25,
        **kwargs
    ):
        # Style the permanent path left behind
        mobject.set_color(path_color)
        mobject.set_stroke(opacity=path_stroke_opacity)

        # Style the temporary passing flash
        flash_mobject = mobject.copy()
        flash_mobject.set_color(flash_color)
        flash_mobject.set_stroke(
            width=flash_stroke_width,
            opacity=flash_stroke_opacity
        )

        super().__init__(
            Create(mobject, **kwargs),
            ShowPassingFlash(flash_mobject, time_width=time_width, **kwargs),
            lag_ratio=0
        )



class AdvancedNestedCaption(Succession):
    """
    Note: This class requires the NestedSplitTex and NestedSplitMathTex classes to function correctly.
    It relies entirely on the nested VGroup structure provided by those two custom classes to apply dual-layer lag ratios.
    """
    def __init__(
        self,
        text_obj,                # This is your NestedSplitTex or NestedSplitMathTex object.
        anim_style="fade_shift", # This defines the entrance style of the animation.
        char_lag_ratio=0.15,     # This controls the delay between individual characters.
        word_lag_ratio=0.4,      # This controls the delay between separate words or math blocks.
        fadein_shift=None,       # This defines the direction and distance of the fade-in movement.
        fadeout_shift=None,      # This defines the direction and distance of the fade-out movement.
        sub_runtime=0.4,         # This determines the runtime for each individual character animation.
        wait_time=1.0,           # This sets how long the full text stays visible on screen.
        alignment="center",      # This positions the text layout on the screen environment.
        speedinfo=None,          # This enables audio syncing via the ChangeSpeed class.
        **kwargs
    ):
        # Note: The alignment configuration positions the main text object across the screen.
        if alignment == "left":
            text_obj.to_edge(LEFT, buff=1)
        elif alignment == "right":
            text_obj.to_edge(RIGHT, buff=1)
        elif alignment == "center":
            text_obj.move_to(ORIGIN)

        if fadein_shift is None:
            fadein_shift = UP * 0.3
        if fadeout_shift is None:
            fadeout_shift = DOWN * 0.3

        word_anims = []
        
        # Note: This loop iterates through each word block to extract character elements.
        for word_vgroup in text_obj:
            char_anims = []
            
            # Note: This handles safely extracting single elements if no sub-mobjects exist.
            sub_mobs = word_vgroup.submobjects if len(word_vgroup.submobjects) > 0 else [word_vgroup]
            
            # Note: Individual character animations are generated based on the selected style.
            for char in sub_mobs:
                if anim_style == "write":
                    char_anims.append(Write(char, run_time=sub_runtime))
                elif anim_style == "fade":
                    char_anims.append(FadeIn(char, run_time=sub_runtime))
                else:
                    char_anims.append(FadeIn(char, shift=fadein_shift, run_time=sub_runtime))
            
            # Note: Character level animations are bundled together using the char_lag_ratio parameter.
            word_anim = LaggedStart(*char_anims, lag_ratio=char_lag_ratio, rate_func=linear)
            word_anims.append(word_anim)
        
        # Note: All word groups are synchronized together using the primary word_lag_ratio setting.
        entry_animation = LaggedStart(*word_anims, lag_ratio=word_lag_ratio)

        # Note: The ChangeSpeed wrapper is applied here if time syncing parameters are provided.
        if speedinfo is not None:
            entry_animation = ChangeSpeed(entry_animation, speedinfo=speedinfo)

        # Note: The parent succession sequence links the entry animation, wait period, and exit fadeout.
        super().__init__(
            entry_animation,
            Wait(wait_time),
            FadeOut(text_obj, shift=fadeout_shift, run_time=0.4),
            **kwargs
        )

