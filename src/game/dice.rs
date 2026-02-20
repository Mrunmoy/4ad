use rand::Rng;

/// Rolls a single six-sided die.
pub fn roll_d6() -> u8 {
    rand::thread_rng().gen_range(1..=6)
}

pub fn roll_2d6() -> u8 {
    roll_d6() + roll_d6()
}

pub fn roll_d66() -> u8 {
    let tens = roll_d6();
    let ones = roll_d6();
    tens * 10 + ones
}

pub fn roll_explosive_d6() -> u16 {
    let mut total = 0;
    loop {
        let roll = roll_d6();
        total += roll as u16;
        if roll != 6 {
            break total;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roll_d6_returns_value_in_range() {
        for _ in 0..1000 {
            let result = roll_d6();
            assert!(
                (1..=6).contains(&result),
                "roll_d6() returned {}, which is outside 1..=6",
                result
            );
        }
    }

    #[test]
    fn roll_2d6_returns_value_in_range() {
        // 2d6 = sum of two d6 rolls, so the range is 2..=12
        for _ in 0..1000 {
            let result = roll_2d6();
            assert!(
                (2..=12).contains(&result),
                "roll_2d6() returned {}, which is outside 2..=12",
                result
            );
        }
    }

    #[test]
    fn roll_explosive_d6_minimum_is_1() {
        // Explosive d6 must be at least 1 (can't roll zero)
        for _ in 0..1000 {
            let result = roll_explosive_d6();
            assert!(result >= 1, "roll_explosive_d6() returned {}", result);
        }
    }

    #[test]
    fn roll_explosive_d6_never_returns_6() {
        // If the die "explodes" on 6, the final total is always
        // either 1-5 (no explosion) or 7+ (at least one explosion).
        // So the result can NEVER be exactly 6.
        for _ in 0..10000 {
            let result = roll_explosive_d6();
            assert!(result != 6, "roll_explosive_d6() should never return exactly 6");
        }
    }

    #[test]
    fn roll_d66_returns_valid_values() {
        // d66 = first d6 as tens digit, second as ones digit
        // Valid values: 11,12,13,14,15,16,21,22,...,65,66
        // So tens digit is 1..=6 and ones digit is 1..=6
        for _ in 0..1000 {
            let result = roll_d66();
            let tens = result / 10;
            let ones = result % 10;
            assert!(
                (1..=6).contains(&tens) && (1..=6).contains(&ones),
                "roll_d66() returned {}, which is not a valid d66 value",
                result
            );
        }
    }
}
