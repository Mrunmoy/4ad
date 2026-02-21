use std::time::{Duration, Instant};

/// A brief dice rolling animation that shows random numbers before
/// revealing the actual result.
///
/// ## Rust concept: `std::time::Instant` for timing
///
/// `Instant` is a monotonic clock — it always moves forward and is
/// immune to system clock adjustments. `Instant::now()` captures
/// the current time, and `instant.elapsed()` returns a `Duration`
/// since that capture. This is the equivalent of C++'s
/// `std::chrono::steady_clock`.
///
/// We use it to time the animation: start the clock when the roll
/// begins, and check `elapsed() >= FRAME_DURATION` to advance frames.
///
/// ## Rust concept: `Duration` for time spans
///
/// `Duration::from_millis(50)` creates a 50ms time span. Duration
/// values can be compared with `>=`, `<=`, etc. This is cleaner than
/// working with raw millisecond integers.
pub struct DiceAnimation {
    /// When the animation started.
    start: Instant,
    /// How many frames to show before revealing the result.
    total_frames: u8,
    /// Current frame index (0-based).
    current_frame: u8,
    /// The actual die result to reveal at the end.
    result: u8,
    /// Label describing what was rolled (e.g., "Attack roll", "d66").
    pub label: String,
    /// Pre-generated random frame values to display during animation.
    frames: Vec<u8>,
}

/// Duration of each animation frame.
const FRAME_DURATION: Duration = Duration::from_millis(60);

/// Total animation time (~360ms for 6 frames at 60ms each).
const TOTAL_FRAMES: u8 = 6;

impl DiceAnimation {
    /// Create a new dice animation.
    ///
    /// `result`: the actual die roll to reveal at the end.
    /// `max_value`: the maximum die value (6 for d6, 66 for d66).
    /// `label`: what was rolled (e.g., "Attack roll").
    pub fn new(result: u8, max_value: u8, label: String) -> DiceAnimation {
        // Generate random frame values
        let frames: Vec<u8> = (0..TOTAL_FRAMES)
            .map(|_| crate::game::dice::roll_d6().min(max_value).max(1))
            .collect();

        DiceAnimation {
            start: Instant::now(),
            total_frames: TOTAL_FRAMES,
            current_frame: 0,
            result,
            label,
            frames,
        }
    }

    /// Advance the animation based on elapsed time.
    /// Returns true if the animation is still running.
    pub fn tick(&mut self) -> bool {
        let elapsed = self.start.elapsed();
        let expected_frame = (elapsed.as_millis() / FRAME_DURATION.as_millis()) as u8;
        self.current_frame = expected_frame.min(self.total_frames);
        self.current_frame < self.total_frames
    }

    /// Whether the animation is complete.
    pub fn is_done(&self) -> bool {
        self.current_frame >= self.total_frames
    }

    /// The value to display right now.
    /// During animation: a random frame value.
    /// After animation: the actual result.
    pub fn display_value(&self) -> u8 {
        if self.is_done() {
            self.result
        } else {
            self.frames
                .get(self.current_frame as usize)
                .copied()
                .unwrap_or(self.result)
        }
    }

    /// The final result.
    pub fn result(&self) -> u8 {
        self.result
    }

    /// How long to wait before the next frame.
    /// Used by the event loop to set `poll` timeout.
    pub fn poll_duration(&self) -> Duration {
        FRAME_DURATION
    }
}

/// Unicode die faces for d6 values (1-6).
/// These are the standard Unicode die face characters (U+2680 to U+2685).
pub fn die_face(value: u8) -> char {
    match value {
        1 => '\u{2680}', // ⚀
        2 => '\u{2681}', // ⚁
        3 => '\u{2682}', // ⚂
        4 => '\u{2683}', // ⚃
        5 => '\u{2684}', // ⚄
        6 => '\u{2685}', // ⚅
        _ => '?',
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn animation_starts_not_done() {
        let anim = DiceAnimation::new(4, 6, "Test".to_string());
        assert!(!anim.is_done());
    }

    #[test]
    fn animation_has_correct_result() {
        let anim = DiceAnimation::new(5, 6, "Attack".to_string());
        assert_eq!(anim.result(), 5);
    }

    #[test]
    fn animation_completes_after_time() {
        let mut anim = DiceAnimation::new(3, 6, "Test".to_string());
        // Fast-forward by replacing start time
        anim.start = Instant::now() - Duration::from_millis(500);
        assert!(!anim.tick()); // should be done
        assert!(anim.is_done());
    }

    #[test]
    fn done_animation_shows_result() {
        let mut anim = DiceAnimation::new(6, 6, "Test".to_string());
        anim.start = Instant::now() - Duration::from_millis(500);
        anim.tick();
        assert_eq!(anim.display_value(), 6);
    }

    #[test]
    fn animation_label_preserved() {
        let anim = DiceAnimation::new(1, 6, "d66 room".to_string());
        assert_eq!(anim.label, "d66 room");
    }

    #[test]
    fn die_faces_are_valid_unicode() {
        assert_eq!(die_face(1), '\u{2680}');
        assert_eq!(die_face(6), '\u{2685}');
    }

    #[test]
    fn die_face_invalid_returns_question_mark() {
        assert_eq!(die_face(0), '?');
        assert_eq!(die_face(7), '?');
    }

    #[test]
    fn poll_duration_is_reasonable() {
        let anim = DiceAnimation::new(1, 6, "Test".to_string());
        let dur = anim.poll_duration();
        assert!(dur.as_millis() >= 30 && dur.as_millis() <= 200);
    }
}
