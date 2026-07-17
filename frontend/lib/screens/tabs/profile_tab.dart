import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../data/strings.dart';
import '../../models/language.dart';
import '../../state/app_state.dart';
import '../../widgets/factor_tile.dart';
import '../../widgets/segmented_toggle.dart';
import '../../widgets/sleep_bar_chart.dart';

class ProfileTab extends StatelessWidget {
  const ProfileTab({super.key});

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final t = app.t;
    final dayLabels = dayTranslations[app.lang]!;

    return ListView(
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(app.fullName?.isNotEmpty == true ? app.fullName! : t.fullName,
                      style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: Color(0xFFEDE7E2))),
                  const SizedBox(height: 3),
                  Text('${app.age} ${t.yearsOld}', style: const TextStyle(fontSize: 13, color: Color(0x73EDE7E2))),
                ],
              ),
            ),
            Container(
              width: 56,
              height: 56,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF392A48), Color(0xFF6B5484)],
                ),
              ),
              child: Center(
                child: Text(_initials(app.fullName),
                    style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700, color: Color(0xFFEDE7E2))),
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),
        _Card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(t.sleepThisWeek, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0x8CEDE7E2))),
              const SizedBox(height: 16),
              SleepBarChart(hoursByDay: app.weeklySleepHours, dayLabels: dayLabels),
              const SizedBox(height: 18),
              Row(
                children: [
                  Expanded(child: _StatTile(label: t.avgSleep, value: app.avgSleepTimeDisplay ?? '—')),
                  const SizedBox(width: 10),
                  Expanded(child: _StatTile(label: t.avgWake, value: app.avgWakeTimeDisplay ?? '—')),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        Text(t.sleepInfluencers, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0x8CEDE7E2))),
        const SizedBox(height: 12),
        _Card(
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              for (var i = 0; i < app.sleepFactors.length; i++)
                FactorTile(
                  name: factorNameTranslations[app.lang]![app.sleepFactors[i].nameKey] ?? app.sleepFactors[i].nameKey,
                  level: app.sleepFactors[i].level,
                  levelLabel: t.levelLabel(app.sleepFactors[i].level),
                  loggedDuringLabel: t.loggedDuring,
                  showDivider: i != app.sleepFactors.length - 1,
                  expanded: app.expandedFactorKey == app.sleepFactors[i].nameKey,
                  onToggle: () => app.toggleFactor(app.sleepFactors[i].nameKey),
                  occurrences: app.sleepFactors[i]
                      .occurrences
                      .map((occ) => TranslatedOccurrence(
                            label: checkinLabelTranslations[app.lang]![occ.checkinLabelKey] ?? occ.checkinLabelKey,
                            time: translateTimeWords(occ.time, app.lang),
                          ))
                      .toList(),
                ),
            ],
          ),
        ),
        const SizedBox(height: 10),
        Text(t.autoDetected, style: const TextStyle(fontSize: 11, color: Color(0x4DEDE7E2))),
        const SizedBox(height: 24),
        Text(t.settings, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0x8CEDE7E2))),
        const SizedBox(height: 12),
        _Card(
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              _SettingsRow(label: t.reminderTone, trailing: Text(t.chimes, style: const TextStyle(fontSize: 13, color: Color(0x66EDE7E2)))),
              _SettingsRow(
                label: t.quietHours,
                trailing: GestureDetector(
                  onTap: () => _showQuietHoursDialog(context, app),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(app.quietHoursDisplay, style: const TextStyle(fontSize: 13, color: Color(0x66EDE7E2))),
                      const SizedBox(width: 6),
                      const Icon(Icons.chevron_right, size: 14, color: Color(0x4DEDE7E2)),
                    ],
                  ),
                ),
              ),
              _SettingsRow(
                label: t.bedtimeMode,
                description: t.bedtimeDesc,
                trailing: _BedtimeSwitch(value: app.bedtimeMode, onChanged: (_) => app.toggleBedtime()),
                showDivider: false,
              ),
            ],
          ),
        ),
        const SizedBox(height: 4),
        _Card(
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              _SettingsRow(
                label: t.age,
                showDivider: false,
                trailing: app.isEditingAge
                    ? Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          SizedBox(
                            width: 56,
                            child: TextField(
                              autofocus: true,
                              keyboardType: TextInputType.number,
                              textAlign: TextAlign.right,
                              controller: TextEditingController(text: app.ageDraft)
                                ..selection = TextSelection.collapsed(offset: app.ageDraft.length),
                              onChanged: app.updateAgeDraft,
                              onSubmitted: (_) => app.saveAge(),
                              style: const TextStyle(fontSize: 13, color: Color(0xFFEDE7E2)),
                              decoration: InputDecoration(
                                filled: true,
                                fillColor: const Color(0x0FFFFFFF),
                                contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(8),
                                  borderSide: const BorderSide(color: Color(0x1FFFFFFF)),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          GestureDetector(
                            onTap: app.saveAge,
                            child: Text(t.save, style: const TextStyle(fontSize: 12.5, color: Color(0xFFB7A6C9))),
                          ),
                        ],
                      )
                    : GestureDetector(
                        onTap: app.startEditAge,
                        child: Text('${app.age}', style: const TextStyle(fontSize: 13, color: Color(0x66EDE7E2))),
                      ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 4),
        _Card(
          padding: EdgeInsets.zero,
          child: _SettingsRow(
            label: t.language,
            showDivider: false,
            trailing: SegmentedToggle(
              expand: false,
              fontSize: 12,
              segmentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              activeColor: const Color(0xFF392A48),
              activeTextColor: const Color(0xFFEDE7E2),
              inactiveTextColor: const Color(0x73EDE7E2),
              trackColor: const Color(0x0DFFFFFF),
              options: [
                SegmentOption(label: 'EN', selected: app.lang == AppLanguage.en, onTap: () => app.setLang(AppLanguage.en)),
                SegmentOption(label: 'ID', selected: app.lang == AppLanguage.id, onTap: () => app.setLang(AppLanguage.id)),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        Material(
          color: const Color(0x1FE06E5A),
          borderRadius: BorderRadius.circular(16),
          child: InkWell(
            borderRadius: BorderRadius.circular(16),
            onTap: app.logOut,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 15),
              child: Text(
                t.logOut,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.w700, color: Color(0xFFE88C77)),
              ),
            ),
          ),
        ),
        const SizedBox(height: 24),
      ],
    );
  }
}

Future<void> _showQuietHoursDialog(BuildContext context, AppState app) async {
  final t = app.t;
  TimeOfDay start = _parseHHmm(app.quietHoursStart);
  TimeOfDay end = _parseHHmm(app.quietHoursEnd);

  final result = await showDialog<(TimeOfDay, TimeOfDay)>(
    context: context,
    builder: (dialogContext) {
      return StatefulBuilder(
        builder: (context, setState) {
          return AlertDialog(
            backgroundColor: const Color(0xFF1F1B2E),
            title: Text(t.quietHours, style: const TextStyle(color: Color(0xFFEDE7E2), fontWeight: FontWeight.w700)),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _QuietHoursTimeRow(
                  label: t.quietHoursStartLabel,
                  time: start,
                  onTap: () async {
                    final picked = await showTimePicker(context: context, initialTime: start);
                    if (picked != null) setState(() => start = picked);
                  },
                ),
                const SizedBox(height: 12),
                _QuietHoursTimeRow(
                  label: t.quietHoursEndLabel,
                  time: end,
                  onTap: () async {
                    final picked = await showTimePicker(context: context, initialTime: end);
                    if (picked != null) setState(() => end = picked);
                  },
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext),
                child: Text(t.cancel, style: const TextStyle(color: Color(0x99EDE7E2))),
              ),
              TextButton(
                onPressed: () => Navigator.pop(dialogContext, (start, end)),
                child: Text(t.save, style: const TextStyle(color: Color(0xFFB7A6C9), fontWeight: FontWeight.w600)),
              ),
            ],
          );
        },
      );
    },
  );

  if (result != null) {
    await app.updateQuietHours(_formatHHmm(result.$1), _formatHHmm(result.$2));
  }
}

class _QuietHoursTimeRow extends StatelessWidget {
  const _QuietHoursTimeRow({required this.label, required this.time, required this.onTap});

  final String label;
  final TimeOfDay time;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 13.5, color: Color(0xFFEDE7E2))),
        GestureDetector(
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0x0AFFFFFF),
              border: Border.all(color: const Color(0x14FFFFFF)),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(time.format(context), style: const TextStyle(fontSize: 13, color: Color(0xFFEDE7E2))),
          ),
        ),
      ],
    );
  }
}

TimeOfDay _parseHHmm(String hhmm) {
  final parts = hhmm.split(':');
  return TimeOfDay(hour: int.tryParse(parts[0]) ?? 0, minute: parts.length > 1 ? int.tryParse(parts[1]) ?? 0 : 0);
}

String _formatHHmm(TimeOfDay time) =>
    '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';

String _initials(String? fullName) {
  if (fullName == null || fullName.trim().isEmpty) return '?';
  final parts = fullName.trim().split(RegExp(r'\s+'));
  final first = parts.first.substring(0, 1);
  final last = parts.length > 1 ? parts.last.substring(0, 1) : '';
  return (first + last).toUpperCase();
}

class _Card extends StatelessWidget {
  const _Card({required this.child, this.padding = const EdgeInsets.all(20)});

  final Widget child;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding,
      decoration: BoxDecoration(color: const Color(0xFF1F1B2E), borderRadius: BorderRadius.circular(20)),
      child: child,
    );
  }
}

class _StatTile extends StatelessWidget {
  const _StatTile({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(color: const Color(0x0AFFFFFF), borderRadius: BorderRadius.circular(14)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 11, color: Color(0x66EDE7E2))),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Color(0xFFEDE7E2))),
        ],
      ),
    );
  }
}

class _SettingsRow extends StatelessWidget {
  const _SettingsRow({required this.label, this.description, required this.trailing, this.showDivider = true});

  final String label;
  final String? description;
  final Widget trailing;
  final bool showDivider;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: showDivider ? const Border(bottom: BorderSide(color: Color(0x0FEDE7E2))) : null,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(fontSize: 14.5, color: Color(0xFFEDE7E2))),
                if (description != null) ...[
                  const SizedBox(height: 2),
                  Text(description!, style: const TextStyle(fontSize: 12, color: Color(0x66EDE7E2))),
                ],
              ],
            ),
          ),
          trailing,
        ],
      ),
    );
  }
}

class _BedtimeSwitch extends StatelessWidget {
  const _BedtimeSwitch({required this.value, required this.onChanged});

  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => onChanged(!value),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        width: 44,
        height: 26,
        padding: const EdgeInsets.all(2),
        decoration: BoxDecoration(
          color: value ? const Color(0xFF6B5484) : const Color(0x26EDE7E2),
          borderRadius: BorderRadius.circular(100),
        ),
        child: AnimatedAlign(
          duration: const Duration(milliseconds: 300),
          alignment: value ? Alignment.centerRight : Alignment.centerLeft,
          child: Container(
            width: 22,
            height: 22,
            decoration: const BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
              boxShadow: [BoxShadow(color: Color(0x4D000000), blurRadius: 3, offset: Offset(0, 1))],
            ),
          ),
        ),
      ),
    );
  }
}
