import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../data/strings.dart';
import '../../models/recap_entry.dart';
import '../../state/app_state.dart';
import '../../widgets/crescent_moon_icon.dart';
import '../../widgets/filter_pill.dart';
import '../../widgets/sun_icon.dart';

class RecapTab extends StatelessWidget {
  const RecapTab({super.key});

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final t = app.t;
    final groups = app.filteredRecapGroups;

    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(t.recap, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700, color: Color(0xFFEDE7E2))),
              const SizedBox(height: 6),
              Text(t.recapSub, style: const TextStyle(fontSize: 13, color: Color(0x73EDE7E2))),
              const SizedBox(height: 20),
              Row(
                children: [
                  FilterPill(
                    label: t.all,
                    selected: app.recapFilter == RecapFilter.all,
                    onTap: () => app.setRecapFilter(RecapFilter.all),
                    activeColor: const Color(0xFF392A48),
                    activeTextColor: const Color(0xFFEDE7E2),
                    inactiveColor: const Color(0x0AFFFFFF),
                    inactiveTextColor: const Color(0x80EDE7E2),
                  ),
                  const SizedBox(width: 8),
                  FilterPill(
                    label: t.nightly,
                    selected: app.recapFilter == RecapFilter.night,
                    onTap: () => app.setRecapFilter(RecapFilter.night),
                    activeColor: const Color(0xFF392A48),
                    activeTextColor: const Color(0xFFEDE7E2),
                    inactiveColor: const Color(0x0AFFFFFF),
                    inactiveTextColor: const Color(0x80EDE7E2),
                  ),
                  const SizedBox(width: 8),
                  FilterPill(
                    label: t.morning,
                    selected: app.recapFilter == RecapFilter.morning,
                    onTap: () => app.setRecapFilter(RecapFilter.morning),
                    activeColor: const Color(0xFF392A48),
                    activeTextColor: const Color(0xFFEDE7E2),
                    inactiveColor: const Color(0x0AFFFFFF),
                    inactiveTextColor: const Color(0x80EDE7E2),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              _MonthFilterRow(app: app, t: t),
              const SizedBox(height: 24),
            ],
          ),
        ),
        if (groups.isEmpty)
          const SliverToBoxAdapter(
            child: Padding(
              padding: EdgeInsets.only(top: 40),
              child: Center(
                child: Text('No check-ins yet', style: TextStyle(color: Color(0x66EDE7E2))),
              ),
            ),
          )
        else
          SliverList(
            delegate: SliverChildBuilderDelegate(
              (context, index) => _RecapGroupSection(group: groups[index], app: app),
              childCount: groups.length,
            ),
          ),
        const SliverToBoxAdapter(child: SizedBox(height: 24)),
      ],
    );
  }
}

class _MonthFilterRow extends StatelessWidget {
  const _MonthFilterRow({required this.app, required this.t});

  final AppState app;
  final UiStrings t;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        GestureDetector(
          onTap: () async {
            final now = DateTime.now();
            final picked = await showDatePicker(
              context: context,
              initialDate: app.selectedMonth ?? now,
              firstDate: DateTime(now.year - 2),
              lastDate: DateTime(now.year + 1),
              helpText: t.month,
            );
            if (picked != null) {
              app.updateSelectedMonth(DateTime(picked.year, picked.month));
            }
          },
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
            decoration: BoxDecoration(
              color: const Color(0x0AFFFFFF),
              border: Border.all(color: const Color(0x14FFFFFF)),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(app.monthFilterLabel, style: const TextStyle(fontSize: 12.5, color: Color(0xFFEDE7E2))),
                const SizedBox(width: 8),
                const Icon(Icons.calendar_today_outlined, size: 14, color: Color(0x80EDE7E2)),
              ],
            ),
          ),
        ),
        if (app.selectedMonth != null) ...[
          const SizedBox(width: 10),
          GestureDetector(
            onTap: app.clearSelectedMonth,
            child: Text(
              t.clear,
              style: const TextStyle(fontSize: 12, color: Color(0x80EDE7E2), decoration: TextDecoration.underline),
            ),
          ),
        ],
      ],
    );
  }
}

class _RecapGroupSection extends StatelessWidget {
  const _RecapGroupSection({required this.group, required this.app});

  final RecapGroup group;
  final AppState app;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            app.recapGroupLabel(group),
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0x8CEDE7E2)),
          ),
          const SizedBox(height: 10),
          ...group.items.map<Widget>((RecapEntry entry) => _RecapEntryRow(
                entry: entry,
                timeDisplay: app.recapItemTimeDisplay(group, entry),
                onTap: () => app.openRecapEntry(entry.id),
              )),
        ],
      ),
    );
  }
}

class _RecapEntryRow extends StatefulWidget {
  const _RecapEntryRow({required this.entry, required this.timeDisplay, required this.onTap});

  final RecapEntry entry;
  final String timeDisplay;

  /// Opens the full chat transcript (RecapDetailScreen).
  final VoidCallback onTap;

  @override
  State<_RecapEntryRow> createState() => _RecapEntryRowState();
}

class _RecapEntryRowState extends State<_RecapEntryRow> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final entry = widget.entry;
    final t = context.watch<AppState>().t;
    final hasFullRecap = (entry.title ?? entry.summary) != null;

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: const Color(0xFF1F1B2E),
        borderRadius: BorderRadius.circular(16),
        child: Column(
          children: [
            InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: hasFullRecap ? () => setState(() => _expanded = !_expanded) : widget.onTap,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                child: Row(
                  children: [
                    Container(
                      width: 34,
                      height: 34,
                      decoration: BoxDecoration(
                        color: entry.isNight ? const Color(0x0FFFFFFF) : const Color(0x26C08A63),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Center(
                        child: entry.isNight
                            ? const CrescentMoonIcon(color: Color(0xFFB7A6C9), size: 15)
                            : const SunIcon(color: Color(0xFFC08A63), size: 14, rayCount: 4),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(widget.timeDisplay, style: const TextStyle(fontSize: 12, color: Color(0x66EDE7E2))),
                          const SizedBox(height: 3),
                          Text(
                            entry.title ?? entry.preview,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 13.5, color: Color(0xFFEDE7E2)),
                          ),
                        ],
                      ),
                    ),
                    AnimatedRotation(
                      duration: const Duration(milliseconds: 200),
                      turns: _expanded ? 0.25 : 0,
                      child: const Icon(Icons.chevron_right, size: 16, color: Color(0x4DEDE7E2)),
                    ),
                  ],
                ),
              ),
            ),
            if (_expanded && hasFullRecap)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (entry.summary != null)
                      Text(
                        entry.summary!,
                        style: const TextStyle(fontSize: 13, height: 1.5, color: Color(0xBFEDE7E2)),
                      ),
                    const SizedBox(height: 12),
                    GestureDetector(
                      onTap: widget.onTap,
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            t.viewFullChat,
                            style: const TextStyle(
                              fontSize: 12.5,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFFB7A6C9),
                            ),
                          ),
                          const SizedBox(width: 4),
                          const Icon(Icons.chevron_right, size: 14, color: Color(0xFFB7A6C9)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
