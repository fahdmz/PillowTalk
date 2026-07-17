import 'package:flutter/material.dart';

import '../state/app_state.dart';

class _NavItemData {
  const _NavItemData(this.tab, this.icon, this.label);
  final HomeTab tab;
  final IconData icon;
  final String label;
}

/// The three-tab bottom bar with a sliding highlight behind the active tab,
/// matching the design's `tabIndicatorLeft` animated position.
class BottomNavBar extends StatelessWidget {
  const BottomNavBar({
    super.key,
    required this.activeTab,
    required this.onSelect,
    required this.recapLabel,
    required this.checkinLabel,
    required this.profileLabel,
  });

  final HomeTab activeTab;
  final ValueChanged<HomeTab> onSelect;
  final String recapLabel;
  final String checkinLabel;
  final String profileLabel;

  static const _activeColor = Color(0xFFEDE7E2);
  static const _inactiveColor = Color(0x66EDE7E2);

  @override
  Widget build(BuildContext context) {
    final items = [
      _NavItemData(HomeTab.recap, Icons.notes_rounded, recapLabel),
      _NavItemData(HomeTab.checkin, Icons.chat_bubble_rounded, checkinLabel),
      _NavItemData(HomeTab.profile, Icons.person_rounded, profileLabel),
    ];
    final activeIndex = items.indexWhere((i) => i.tab == activeTab);

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 28),
      decoration: const BoxDecoration(
        color: Color(0xE5161320),
        border: Border(top: BorderSide(color: Color(0x0FEDE7E2))),
      ),
      child: Stack(
        children: [
          LayoutBuilder(
            builder: (context, constraints) {
              final segmentWidth = constraints.maxWidth / items.length;
              return AnimatedPositioned(
                duration: const Duration(milliseconds: 350),
                curve: Curves.easeOutCubic,
                top: 6,
                left: segmentWidth * activeIndex,
                width: segmentWidth,
                height: 48,
                child: Container(
                  margin: const EdgeInsets.symmetric(horizontal: 2),
                  decoration: BoxDecoration(
                    color: const Color(0x2E6B5484),
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
              );
            },
          ),
          Row(
            children: items
                .map((item) => Expanded(
                      child: GestureDetector(
                        onTap: () => onSelect(item.tab),
                        behavior: HitTestBehavior.opaque,
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              item.icon,
                              size: 20,
                              color: item.tab == activeTab ? _activeColor : _inactiveColor,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              item.label,
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: item.tab == activeTab ? _activeColor : _inactiveColor,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ))
                .toList(),
          ),
        ],
      ),
    );
  }
}
