import 'package:flutter/material.dart';

/// CTA Button Variant
enum CtaButtonVariant {
  /// Active state with bright cyan background (#00DCFF)
  active,
  
  /// Secondary state with semi-transparent white background
  secondary,
  
  /// Disabled state
  disabled,
}

/// CTA (Call-to-Action) Button Widget
/// 
/// Figma Design: Blue/100% (#00DCFF) background with Grey/900 (#18191B) text
/// Default button from design system
class CtaButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final CtaButtonVariant variant;

  const CtaButton({
    super.key,
    required this.text,
    this.onPressed,
    this.variant = CtaButtonVariant.active,
  });

  Color _getBackgroundColor() {
    switch (variant) {
      case CtaButtonVariant.active:
        return const Color(0xFF00DCFF); // Blue/100%
      case CtaButtonVariant.secondary:
        return Colors.white.withOpacity(0.2);
      case CtaButtonVariant.disabled:
        return const Color(0xFF2C2C2E);
    }
  }

  Color _getForegroundColor() {
    switch (variant) {
      case CtaButtonVariant.active:
        return const Color(0xFF18191B); // Grey/900
      case CtaButtonVariant.secondary:
        return const Color(0xFF18191B);
      case CtaButtonVariant.disabled:
        return const Color(0xFF636366);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 54,
      child: ElevatedButton(
        onPressed: variant == CtaButtonVariant.disabled ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: _getBackgroundColor(),
          foregroundColor: _getForegroundColor(),
          disabledBackgroundColor: const Color(0xFF2C2C2E),
          disabledForegroundColor: const Color(0xFF636366),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 10),
        ),
        child: Text(
          text,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w600, // SemiBold
            letterSpacing: -0.3,
          ),
        ),
      ),
    );
  }
}
