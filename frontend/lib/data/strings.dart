import '../models/language.dart';
import '../models/sleep_factor.dart';

class UiStrings {
  const UiStrings({
    required this.tagline,
    required this.logIn,
    required this.signUp,
    required this.fullName,
    required this.email,
    required this.password,
    required this.createAccount,
    required this.footer,
    required this.confirmPassword,
    required this.passwordMismatch,
    required this.orDivider,
    required this.continueWithGmail,
    required this.recap,
    required this.recapSub,
    required this.all,
    required this.nightly,
    required this.morning,
    required this.month,
    required this.clear,
    required this.readyCheckin,
    required this.chooseMoment,
    required this.nightlyCheckin,
    required this.windDown,
    required this.morningCheckin,
    required this.reflect,
    required this.yearsOld,
    required this.sleepThisWeek,
    required this.avgSleep,
    required this.avgWake,
    required this.sleepInfluencers,
    required this.autoDetected,
    required this.loggedDuring,
    required this.settings,
    required this.reminderTone,
    required this.chimes,
    required this.quietHours,
    required this.bedtimeMode,
    required this.bedtimeDesc,
    required this.age,
    required this.save,
    required this.cancel,
    required this.quietHoursStartLabel,
    required this.quietHoursEndLabel,
    required this.language,
    required this.logOut,
    required this.navRecap,
    required this.navCheckin,
    required this.navProfile,
    required this.listeningNoJudgment,
    required this.listening,
    required this.typeOrSpeak,
    required this.voiceInputCaption,
    required this.aiVoiceCaption,
    required this.high,
    required this.medium,
    required this.low,
    required this.micPermTitle,
    required this.micPermBody,
    required this.micPermAllow,
    required this.micPermDeny,
    required this.deleteEntryTitle,
    required this.deleteEntryBody,
    required this.deleteEntryConfirm,
    required this.deleteEntryCancel,
    required this.notifNow,
    required this.previewNightNotif,
    required this.previewMorningNotif,
    required this.notifNightTitle,
    required this.notifNightBody,
    required this.notifMorningTitle,
    required this.notifMorningBody,
    required this.checkinReadOnlyNotice,
    required this.viewFullChat,
  });

  final String tagline, logIn, signUp, fullName, email, password;
  final String createAccount, footer;
  final String confirmPassword, passwordMismatch, orDivider, continueWithGmail;
  final String recap, recapSub, all, nightly, morning, month, clear;
  final String readyCheckin, chooseMoment;
  final String nightlyCheckin, windDown, morningCheckin, reflect;
  final String yearsOld, sleepThisWeek, avgSleep, avgWake;
  final String sleepInfluencers, autoDetected, loggedDuring;
  final String settings, reminderTone, chimes, quietHours;
  final String bedtimeMode, bedtimeDesc;
  final String age, save, cancel, quietHoursStartLabel, quietHoursEndLabel;
  final String language, logOut;
  final String navRecap, navCheckin, navProfile;
  final String listeningNoJudgment, listening, typeOrSpeak;
  final String voiceInputCaption, aiVoiceCaption;
  final String high, medium, low;
  final String micPermTitle, micPermBody, micPermAllow, micPermDeny;
  final String deleteEntryTitle, deleteEntryBody, deleteEntryConfirm, deleteEntryCancel;
  final String notifNow, previewNightNotif, previewMorningNotif;
  final String notifNightTitle, notifNightBody, notifMorningTitle, notifMorningBody;
  final String checkinReadOnlyNotice;
  final String viewFullChat;

  String levelLabel(FactorLevel level) {
    switch (level) {
      case FactorLevel.high:
        return high;
      case FactorLevel.medium:
        return medium;
      case FactorLevel.low:
        return low;
    }
  }
}

const _en = UiStrings(
  tagline: 'a quiet place to wind down',
  logIn: 'Log In',
  signUp: 'Sign Up',
  fullName: 'Full name',
  email: 'Email',
  password: 'Password',
  createAccount: 'Create Account',
  footer: 'No pressure. No streaks. Just rest.',
  confirmPassword: 'Confirm password',
  passwordMismatch: "Passwords don't match",
  orDivider: 'or',
  continueWithGmail: 'Continue with Gmail',
  recap: 'Recap',
  recapSub: 'Your check-in history',
  all: 'All',
  nightly: 'Nightly',
  morning: 'Morning',
  month: 'Month',
  clear: 'Clear',
  readyCheckin: 'Ready to check in?',
  chooseMoment: 'Choose a moment to talk it through',
  nightlyCheckin: 'Nightly Check-in',
  windDown: 'Wind down and talk it through',
  morningCheckin: 'Morning Check-in',
  reflect: 'Reflect on how you slept',
  yearsOld: 'years old',
  sleepThisWeek: 'Sleep this week',
  avgSleep: 'Avg. sleep time',
  avgWake: 'Avg. wake time',
  sleepInfluencers: 'Sleep Influencers',
  autoDetected: 'Auto-detected from your check-ins',
  loggedDuring: 'Logged during these check-ins',
  settings: 'Settings',
  reminderTone: 'Reminder tone',
  chimes: 'Chimes',
  quietHours: 'Quiet hours',
  bedtimeMode: 'Bedtime mode',
  bedtimeDesc: 'Dim and desaturate the screen',
  age: 'Age',
  save: 'Save',
  cancel: 'Cancel',
  quietHoursStartLabel: 'Start',
  quietHoursEndLabel: 'End',
  language: 'Language',
  logOut: 'Log Out',
  navRecap: 'Recap',
  navCheckin: 'Check-in',
  navProfile: 'Profile',
  listeningNoJudgment: 'Listening, no judgment',
  listening: 'Listening…',
  typeOrSpeak: 'Type or speak…',
  voiceInputCaption: 'Voice input — tap to switch to AI voice replies',
  aiVoiceCaption: 'AI reads replies aloud — tap to switch to voice input',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  micPermTitle: 'Allow Microphone Access',
  micPermBody: 'DrowzyDiary uses your microphone to log check-ins by voice. Your audio is never stored.',
  micPermAllow: 'Allow Microphone',
  micPermDeny: 'Not Now',
  deleteEntryTitle: 'Delete this entry?',
  deleteEntryBody: "This check-in and its conversation will be permanently removed. This can't be undone.",
  deleteEntryConfirm: 'Delete Entry',
  deleteEntryCancel: 'Cancel',
  notifNow: 'now',
  previewNightNotif: 'Preview night reminder',
  previewMorningNotif: 'Preview morning reminder',
  notifNightTitle: 'Time to wind down',
  notifNightBody: "It's almost bedtime — log tonight's check-in.",
  notifMorningTitle: 'Good morning',
  notifMorningBody: 'How did you sleep? Log your morning check-in.',
  checkinReadOnlyNotice: "Today's check-in — already logged",
  viewFullChat: 'View full chat',
);

const _id = UiStrings(
  tagline: 'tempat tenang untuk bersantai',
  logIn: 'Masuk',
  signUp: 'Daftar',
  fullName: 'Nama lengkap',
  email: 'Email',
  password: 'Kata sandi',
  createAccount: 'Buat Akun',
  footer: 'Tanpa tekanan. Tanpa target harian. Cukup istirahat.',
  confirmPassword: 'Konfirmasi kata sandi',
  passwordMismatch: 'Kata sandi tidak cocok',
  orDivider: 'atau',
  continueWithGmail: 'Lanjutkan dengan Gmail',
  recap: 'Rekap',
  recapSub: 'Riwayat check-in kamu',
  all: 'Semua',
  nightly: 'Malam',
  morning: 'Pagi',
  month: 'Bulan',
  clear: 'Hapus',
  readyCheckin: 'Siap check-in?',
  chooseMoment: 'Pilih waktu untuk bercerita',
  nightlyCheckin: 'Check-in Malam',
  windDown: 'Bersantai dan bercerita',
  morningCheckin: 'Check-in Pagi',
  reflect: 'Renungkan tidurmu semalam',
  yearsOld: 'tahun',
  sleepThisWeek: 'Tidur minggu ini',
  avgSleep: 'Rata-rata waktu tidur',
  avgWake: 'Rata-rata waktu bangun',
  sleepInfluencers: 'Pengaruh Tidur',
  autoDetected: 'Terdeteksi otomatis dari check-in kamu',
  loggedDuring: 'Tercatat selama check-in berikut',
  settings: 'Pengaturan',
  reminderTone: 'Nada pengingat',
  chimes: 'Lonceng',
  quietHours: 'Jam tenang',
  bedtimeMode: 'Mode tidur',
  bedtimeDesc: 'Redupkan dan kurangi saturasi layar',
  age: 'Usia',
  save: 'Simpan',
  cancel: 'Batal',
  quietHoursStartLabel: 'Mulai',
  quietHoursEndLabel: 'Selesai',
  language: 'Bahasa',
  logOut: 'Keluar',
  navRecap: 'Rekap',
  navCheckin: 'Check-in',
  navProfile: 'Profil',
  listeningNoJudgment: 'Mendengarkan, tanpa menghakimi',
  listening: 'Mendengarkan…',
  typeOrSpeak: 'Ketik atau bicara…',
  voiceInputCaption: 'Input suara — ketuk untuk beralih ke balasan suara AI',
  aiVoiceCaption: 'AI membacakan balasan — ketuk untuk beralih ke input suara',
  high: 'Tinggi',
  medium: 'Sedang',
  low: 'Rendah',
  micPermTitle: 'Izinkan Akses Mikrofon',
  micPermBody: 'DrowzyDiary menggunakan mikrofon untuk mencatat check-in lewat suara. Audio kamu tidak pernah disimpan.',
  micPermAllow: 'Izinkan Mikrofon',
  micPermDeny: 'Nanti Saja',
  deleteEntryTitle: 'Hapus entri ini?',
  deleteEntryBody: 'Check-in ini beserta percakapannya akan dihapus permanen. Tindakan ini tidak bisa dibatalkan.',
  deleteEntryConfirm: 'Hapus Entri',
  deleteEntryCancel: 'Batal',
  notifNow: 'sekarang',
  previewNightNotif: 'Pratinjau pengingat malam',
  previewMorningNotif: 'Pratinjau pengingat pagi',
  notifNightTitle: 'Waktunya bersantai',
  notifNightBody: 'Hampir waktu tidur — catat check-in malam ini.',
  notifMorningTitle: 'Selamat pagi',
  notifMorningBody: 'Bagaimana tidurmu? Catat check-in pagi kamu.',
  checkinReadOnlyNotice: 'Check-in hari ini — sudah tercatat',
  viewFullChat: 'Lihat percakapan lengkap',
);

UiStrings uiStringsFor(AppLanguage lang) => lang == AppLanguage.en ? _en : _id;

const dateLabelTranslations = <AppLanguage, Map<String, String>>{
  AppLanguage.en: {
    'Today': 'Today',
    'Yesterday': 'Yesterday',
    'Monday': 'Monday',
    'Tuesday': 'Tuesday',
    'Wednesday': 'Wednesday',
    'Thursday': 'Thursday',
    'Friday': 'Friday',
    'Saturday': 'Saturday',
    'Sunday': 'Sunday',
    'Last week': 'Last week',
  },
  AppLanguage.id: {
    'Today': 'Hari ini',
    'Yesterday': 'Kemarin',
    'Monday': 'Senin',
    'Tuesday': 'Selasa',
    'Wednesday': 'Rabu',
    'Thursday': 'Kamis',
    'Friday': 'Jumat',
    'Saturday': 'Sabtu',
    'Sunday': 'Minggu',
    'Last week': 'Minggu lalu',
  },
};

const dayTranslations = <AppLanguage, List<String>>{
  AppLanguage.en: ['M', 'T', 'W', 'T', 'F', 'S', 'S'],
  AppLanguage.id: ['S', 'S', 'R', 'K', 'J', 'S', 'M'],
};

const factorNameTranslations = <AppLanguage, Map<String, String>>{
  AppLanguage.en: {
    'Late caffeine intake': 'Late caffeine intake',
    'Screen time before bed': 'Screen time before bed',
    'Work-related stress': 'Work-related stress',
    'Irregular bedtime schedule': 'Irregular bedtime schedule',
  },
  AppLanguage.id: {
    'Late caffeine intake': 'Kafein larut malam',
    'Screen time before bed': 'Waktu layar sebelum tidur',
    'Work-related stress': 'Stres pekerjaan',
    'Irregular bedtime schedule': 'Jadwal tidur tidak teratur',
  },
};

const checkinLabelTranslations = <AppLanguage, Map<String, String>>{
  AppLanguage.en: {
    'Nightly Check-in': 'Nightly Check-in',
    'Morning Check-in': 'Morning Check-in',
  },
  AppLanguage.id: {
    'Nightly Check-in': 'Check-in Malam',
    'Morning Check-in': 'Check-in Pagi',
  },
};

const _timeWordTranslationsId = {
  'Today': 'Hari ini',
  'Yesterday': 'Kemarin',
  'Monday': 'Senin',
  'Tuesday': 'Selasa',
  'Wednesday': 'Rabu',
  'Thursday': 'Kamis',
  'Friday': 'Jumat',
  'Saturday': 'Sabtu',
  'Sunday': 'Minggu',
  'Last week': 'Minggu lalu',
};

/// Ports the design's `translateTimeWords`: swaps English day/relative-date
/// words embedded inside an occurrence timestamp string when in Indonesian.
String translateTimeWords(String value, AppLanguage lang) {
  if (lang == AppLanguage.en) return value;
  var out = value;
  for (final entry in _timeWordTranslationsId.entries) {
    out = out.replaceAll(entry.key, entry.value);
  }
  return out;
}
