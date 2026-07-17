import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../state/app_state.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/star_field_background.dart';
import 'recap_detail_screen.dart';
import 'tabs/checkin_tab.dart';
import 'tabs/profile_tab.dart';
import 'tabs/recap_tab.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();

    return Container(
      color: const Color(0xFF161320),
      child: Stack(
        children: [
          const Positioned.fill(child: StarFieldBackground()),
          Column(
            children: [
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(24, 60, 24, 24),
                  child: IndexedStack(
                    index: app.activeTab.index,
                    children: const [RecapTab(), CheckinTab(), ProfileTab()],
                  ),
                ),
              ),
              BottomNavBar(
                activeTab: app.activeTab,
                onSelect: app.setTab,
                recapLabel: app.t.navRecap,
                checkinLabel: app.t.navCheckin,
                profileLabel: app.t.navProfile,
              ),
            ],
          ),
          if (app.openEntry != null) const RecapDetailScreen(),
        ],
      ),
    );
  }
}
