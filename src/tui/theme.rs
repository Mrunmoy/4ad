use ratatui::style::{Color, Modifier, Style};

/// Centralized color theme for the TUI.
///
/// ## Rust concept: associated constants on a struct
///
/// Instead of scattering color values across the codebase, we define
/// them as `const` items in a single module. In C++, you'd use a
/// namespace with `constexpr` values. In Rust, we use a zero-size
/// struct with associated constants — the struct is never instantiated,
/// it's just a namespace.
///
/// Every color decision in the UI references this module, so changing
/// the theme means editing one file.
pub struct Theme;

impl Theme {
    // === Health bars ===

    /// Health above 66% — character is doing fine.
    pub const HEALTH_HIGH: Color = Color::Green;
    /// Health between 33% and 66% — getting hurt.
    pub const HEALTH_MED: Color = Color::Yellow;
    /// Health below 33% — in danger.
    pub const HEALTH_LOW: Color = Color::Red;
    /// Dead character text.
    pub const DEAD: Color = Color::DarkGray;

    // === Combat log colors ===

    /// Damage dealt or taken.
    pub const DAMAGE: Color = Color::Red;
    /// Healing received.
    pub const HEALING: Color = Color::Green;
    /// Spell casting.
    pub const SPELL: Color = Color::Blue;
    /// Treasure and gold found.
    pub const TREASURE: Color = Color::Yellow;
    /// Room entry and exploration.
    pub const EXPLORATION: Color = Color::Cyan;
    /// Neutral log messages.
    pub const LOG_DEFAULT: Color = Color::Gray;

    // === Map colors ===

    /// Wall tiles.
    pub const MAP_WALL: Color = Color::White;
    /// Floor tiles.
    pub const MAP_FLOOR: Color = Color::Gray;
    /// Door tiles.
    pub const MAP_DOOR: Color = Color::Yellow;
    /// Visited room floor (dimmed).
    pub const MAP_VISITED_FLOOR: Color = Color::DarkGray;
    /// Current room highlight background.
    pub const MAP_CURRENT_BG: Color = Color::DarkGray;
    /// Party token `@`.
    pub const PARTY_TOKEN: Color = Color::Yellow;

    // === UI chrome ===

    /// Selected/highlighted item.
    pub const SELECTED: Color = Color::Yellow;
    /// Active control hint.
    pub const CONTROL_HINT: Color = Color::Cyan;
    /// Error messages.
    pub const ERROR: Color = Color::Red;
    /// Section titles.
    pub const TITLE: Color = Color::White;
    /// Muted/disabled text.
    pub const MUTED: Color = Color::DarkGray;
    /// Class name in party panel.
    pub const CLASS_NAME: Color = Color::Cyan;
    /// Level indicator.
    pub const LEVEL: Color = Color::White;
    /// Gold amount.
    pub const GOLD: Color = Color::Yellow;
}

/// Build a health bar string and return the appropriate color.
///
/// ## Rust concept: returning tuples
///
/// Functions can return `(String, Color)` — a tuple of two values.
/// In C++, you'd return `std::pair<std::string, Color>` or use
/// output parameters. Rust tuples are destructured naturally:
///
/// ```ignore
/// let (bar, color) = health_bar(3, 6);
/// ```
///
/// The bar uses filled hearts for remaining life and empty hearts
/// for lost life: `♥♥♥♡♡♡`
pub fn health_bar(current: u8, max: u8) -> (String, Color) {
    let filled = current as usize;
    let empty = (max as usize).saturating_sub(filled);
    let bar = format!(
        "{}{}",
        "♥".repeat(filled),
        "♡".repeat(empty),
    );

    let color = if max == 0 || current == 0 {
        Theme::DEAD
    } else {
        let pct = (current as f32 / max as f32) * 100.0;
        if pct > 66.0 {
            Theme::HEALTH_HIGH
        } else if pct > 33.0 {
            Theme::HEALTH_MED
        } else {
            Theme::HEALTH_LOW
        }
    };

    (bar, color)
}

/// Classify a log message by its content and return the appropriate color.
///
/// This is a simple heuristic based on keywords in the message.
/// The game logic writes structured strings to `game.log`, so we
/// can pattern-match on common words.
pub fn log_color(message: &str) -> Color {
    let lower = message.to_lowercase();
    if lower.contains("damage") || lower.contains("wound") || lower.contains("killed")
        || lower.contains("slain") || lower.contains("hit") || lower.contains("dead")
        || lower.contains("wiped") || lower.contains("dies")
    {
        Theme::DAMAGE
    } else if lower.contains("heal") || lower.contains("restored")
        || lower.contains("recover")
    {
        Theme::HEALING
    } else if lower.contains("spell") || lower.contains("cast")
        || lower.contains("fireball") || lower.contains("lightning")
        || lower.contains("sleep") || lower.contains("blessing")
        || lower.contains("escape") || lower.contains("protect")
    {
        Theme::SPELL
    } else if lower.contains("gold") || lower.contains("treasure")
        || lower.contains("gem") || lower.contains("jewelry")
        || lower.contains("loot")
    {
        Theme::TREASURE
    } else if lower.contains("enter") || lower.contains("room")
        || lower.contains("door") || lower.contains("explore")
        || lower.contains("corridor") || lower.contains("descend")
    {
        Theme::EXPLORATION
    } else {
        Theme::LOG_DEFAULT
    }
}

/// Helper: create a bold style with the given foreground color.
pub fn bold(color: Color) -> Style {
    Style::default().fg(color).add_modifier(Modifier::BOLD)
}

/// Helper: create a plain style with the given foreground color.
pub fn fg(color: Color) -> Style {
    Style::default().fg(color)
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Health bar ---

    #[test]
    fn full_health_is_green() {
        let (bar, color) = health_bar(6, 6);
        assert_eq!(bar, "♥♥♥♥♥♥");
        assert_eq!(color, Theme::HEALTH_HIGH);
    }

    #[test]
    fn high_health_is_green() {
        // 5/6 = 83% > 66%
        let (bar, color) = health_bar(5, 6);
        assert_eq!(bar, "♥♥♥♥♥♡");
        assert_eq!(color, Theme::HEALTH_HIGH);
    }

    #[test]
    fn medium_health_is_yellow() {
        // 3/6 = 50%, between 33% and 66%
        let (bar, color) = health_bar(3, 6);
        assert_eq!(bar, "♥♥♥♡♡♡");
        assert_eq!(color, Theme::HEALTH_MED);
    }

    #[test]
    fn low_health_is_red() {
        // 1/6 = 16% < 33%
        let (bar, color) = health_bar(1, 6);
        assert_eq!(bar, "♥♡♡♡♡♡");
        assert_eq!(color, Theme::HEALTH_LOW);
    }

    #[test]
    fn dead_is_dark_gray() {
        let (bar, color) = health_bar(0, 6);
        assert_eq!(bar, "♡♡♡♡♡♡");
        assert_eq!(color, Theme::DEAD);
    }

    #[test]
    fn zero_max_health_is_dead() {
        let (_, color) = health_bar(0, 0);
        assert_eq!(color, Theme::DEAD);
    }

    // --- Log color classification ---

    #[test]
    fn damage_keywords_are_red() {
        assert_eq!(log_color("Warrior takes 2 damage"), Theme::DAMAGE);
        assert_eq!(log_color("3 goblins slain"), Theme::DAMAGE);
        assert_eq!(log_color("Party member killed"), Theme::DAMAGE);
    }

    #[test]
    fn healing_keywords_are_green() {
        assert_eq!(log_color("Cleric heals 3 HP"), Theme::HEALING);
        assert_eq!(log_color("Life restored"), Theme::HEALING);
    }

    #[test]
    fn spell_keywords_are_blue() {
        assert_eq!(log_color("Wizard casts Fireball"), Theme::SPELL);
        assert_eq!(log_color("Lightning bolt strikes"), Theme::SPELL);
    }

    #[test]
    fn treasure_keywords_are_yellow() {
        assert_eq!(log_color("Found 50 gold"), Theme::TREASURE);
        assert_eq!(log_color("Treasure chest!"), Theme::TREASURE);
    }

    #[test]
    fn exploration_keywords_are_cyan() {
        assert_eq!(log_color("Entered room 5"), Theme::EXPLORATION);
        assert_eq!(log_color("A door to the north"), Theme::EXPLORATION);
    }

    #[test]
    fn unclassified_is_default_gray() {
        assert_eq!(log_color("Something happened"), Theme::LOG_DEFAULT);
    }

    // --- Style helpers ---

    #[test]
    fn bold_helper_creates_bold_style() {
        let style = bold(Color::Red);
        assert_eq!(style.fg, Some(Color::Red));
        assert!(style.add_modifier.contains(Modifier::BOLD));
    }

    #[test]
    fn fg_helper_creates_plain_style() {
        let style = fg(Color::Green);
        assert_eq!(style.fg, Some(Color::Green));
        assert!(!style.add_modifier.contains(Modifier::BOLD));
    }
}
