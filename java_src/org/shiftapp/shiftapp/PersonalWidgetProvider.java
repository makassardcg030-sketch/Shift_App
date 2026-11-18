package org.shiftapp.shiftapp;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.provider.AlarmClock;
import android.view.View;
import android.widget.RemoteViews;
import android.widget.Toast;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public class PersonalWidgetProvider extends AppWidgetProvider {

    private static final String PREFS = "shift_widget";
    private static final String KEY_SCHEDULE = "schedule";
    private static final String KEY_PERSON_PREFIX = "personal_name_";
    private static final String ACTION_REFRESH = "org.shiftapp.shiftapp.PERSONAL_REFRESH";
    private static final String ACTION_SET_ALARM = "org.shiftapp.shiftapp.PERSONAL_SET_ALARM";
    private static final String EXTRA_ALARM_MS = "alarm_target_ms";
    private static final String EXTRA_SHIFT_LABEL = "shift_label";
    private static final long HOUR_MS = 60L * 60L * 1000L;

    static class Entry {
        String name;
        int hour;
        int dur;
        long start;
        long end;
    }

    @Override
    public void onUpdate(Context context, AppWidgetManager manager, int[] appWidgetIds) {
        for (int id : appWidgetIds) {
            updateWidget(context, manager, id);
        }
        scheduleNext(context);
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        super.onReceive(context, intent);
        if (intent == null || intent.getAction() == null) {
            return;
        }
        String action = intent.getAction();
        if (ACTION_REFRESH.equals(action)) {
            updateAll(context);
        } else if (ACTION_SET_ALARM.equals(action)) {
            long targetMs = intent.getLongExtra(EXTRA_ALARM_MS, -1L);
            String label = intent.getStringExtra(EXTRA_SHIFT_LABEL);
            triggerSystemAlarm(context, targetMs, label);
        }
    }

    @Override
    public void onDeleted(Context context, int[] appWidgetIds) {
        SharedPreferences.Editor ed = prefs(context).edit();
        for (int id : appWidgetIds) {
            ed.remove(KEY_PERSON_PREFIX + id);
        }
        ed.apply();
    }

    @Override
    public void onDisabled(Context context) {
        AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (am != null) {
            am.cancel(refreshIntent(context));
        }
    }

    public static void saveSelectedName(Context context, int widgetId, String name) {
        prefs(context).edit().putString(KEY_PERSON_PREFIX + widgetId, name).apply();
    }

    public static String getSelectedName(Context context, int widgetId) {
        return prefs(context).getString(KEY_PERSON_PREFIX + widgetId, "");
    }

    public static List<String> getAvailableNames(Context context) {
        Set<String> names = new LinkedHashSet<String>();
        for (Entry e : parse(prefs(context).getString(KEY_SCHEDULE, ""))) {
            if (e.name != null && !e.name.isEmpty()) {
                names.add(e.name);
            }
        }
        return new ArrayList<String>(names);
    }

    public static void updateAll(Context context) {
        AppWidgetManager manager = AppWidgetManager.getInstance(context);
        ComponentName cn = new ComponentName(context, PersonalWidgetProvider.class);
        int[] ids = manager.getAppWidgetIds(cn);
        for (int id : ids) {
            updateWidget(context, manager, id);
        }
        scheduleNext(context);
    }

    static void updateWidget(Context context, AppWidgetManager manager, int widgetId) {
        String pkg = context.getPackageName();
        int layoutId = context.getResources().getIdentifier("personal_widget", "layout", pkg);
        if (layoutId == 0) {
            return;
        }
        RemoteViews views = new RemoteViews(pkg, layoutId);
        WidgetTheme.Palette th = WidgetTheme.load(context);
        WidgetTheme.bg(views, context, "pwidget_root", th.bg);
        WidgetTheme.fg(views, context, "pwidget_name", th.text);
        WidgetTheme.fg(views, context, "p_time", th.nextBg);
        WidgetTheme.bg(views, context, "p_duty_row", th.accent);
        WidgetTheme.fg(views, context, "p_duty_label", th.onAccent);
        WidgetTheme.fg(views, context, "pwidget_duty", th.onAccent);
        WidgetTheme.bg(views, context, "p_next_row", th.nextBg);
        WidgetTheme.fg(views, context, "p_next_label", th.nextText);
        WidgetTheme.fg(views, context, "pwidget_next", th.nextText);
        String selectedName = getSelectedName(context, widgetId);
        String raw = prefs(context).getString(KEY_SCHEDULE, "");
        List<Entry> all = parse(raw);
        long now = System.currentTimeMillis();

        int idName = idOf(context, "pwidget_name");
        int idDuty = idOf(context, "pwidget_duty");
        int idNext = idOf(context, "pwidget_next");
        int idBtnAlarm = idOf(context, "pwidget_btn_alarm");
        int idRoot = idOf(context, "pwidget_root");

        // Ketuk nama untuk membuka dialog ganti nama
        Intent cfgIntent = new Intent(context, PersonalWidgetConfigActivity.class);
        cfgIntent.putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId);
        cfgIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent cfgPi = PendingIntent.getActivity(
                context, widgetId + 1000, cfgIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        views.setOnClickPendingIntent(idName, cfgPi);

        // Ketuk area lain untuk membuka aplikasi utama
        Intent launch = context.getPackageManager().getLaunchIntentForPackage(pkg);
        if (launch != null) {
            PendingIntent launchPi = PendingIntent.getActivity(
                    context, widgetId + 2000, launch,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            views.setOnClickPendingIntent(idRoot, launchPi);
        }

        if (selectedName == null || selectedName.isEmpty()) {
            views.setTextViewText(idName, "Ketuk pilih nama ▼");
            views.setTextViewText(idDuty, "-");
            views.setTextViewText(idNext, "Belum dipilih");
            views.setViewVisibility(idBtnAlarm, View.GONE);
            manager.updateAppWidget(widgetId, views);
            return;
        }

        views.setTextViewText(idName, selectedName + " ✎");

        Entry activeShift = null;
        Entry nextShift = null;
        for (Entry e : all) {
            if (!e.name.equalsIgnoreCase(selectedName)) {
                continue;
            }
            if (e.start <= now && now < e.end) {
                activeShift = e;
            } else if (e.start > now) {
                if (nextShift == null || e.start < nextShift.start) {
                    nextShift = e;
                }
            }
        }

        if (activeShift != null) {
            String endStr = fmt("HH:mm", activeShift.end);
            views.setTextViewText(idDuty, activeShift.hour + "+" + activeShift.dur + " (s/d " + endStr + ")");
        } else {
            views.setTextViewText(idDuty, "Sedang Off / Libur");
        }

        if (nextShift != null) {
            String nextLabel = sameDay(nextShift.start, now)
                    ? "Hari ini " + fmt("HH:mm", nextShift.start)
                    : fmt("EEE, dd MMM HH:mm", nextShift.start);
            views.setTextViewText(idNext, nextLabel);

            long alarmTimeMs = nextShift.start - HOUR_MS;
            String alarmHourStr = fmt("HH:mm", alarmTimeMs);
            views.setViewVisibility(idBtnAlarm, View.VISIBLE);
            views.setTextViewText(idBtnAlarm, "⏰ " + alarmHourStr);

            Intent alarmIntent = new Intent(context, PersonalWidgetProvider.class);
            alarmIntent.setAction(ACTION_SET_ALARM);
            alarmIntent.putExtra(EXTRA_ALARM_MS, alarmTimeMs);
            alarmIntent.putExtra(EXTRA_SHIFT_LABEL, "Shift " + selectedName + " (" + fmt("HH:mm", nextShift.start) + ")");
            PendingIntent alarmPi = PendingIntent.getBroadcast(
                    context, widgetId + 3000, alarmIntent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            views.setOnClickPendingIntent(idBtnAlarm, alarmPi);
        } else {
            views.setTextViewText(idNext, "Tidak ada jadwal");
            views.setViewVisibility(idBtnAlarm, View.GONE);
        }

        manager.updateAppWidget(widgetId, views);
    }

    private static void triggerSystemAlarm(Context context, long alarmTimeMs, String label) {
        if (alarmTimeMs <= 0L) {
            Toast.makeText(context, "Jadwal berikutnya tidak tersedia.", Toast.LENGTH_SHORT).show();
            return;
        }
        Calendar cal = Calendar.getInstance();
        cal.setTimeInMillis(alarmTimeMs);
        int hour = cal.get(Calendar.HOUR_OF_DAY);
        int minute = cal.get(Calendar.MINUTE);

        Intent intent = new Intent(AlarmClock.ACTION_SET_ALARM);
        intent.putExtra(AlarmClock.EXTRA_HOUR, hour);
        intent.putExtra(AlarmClock.EXTRA_MINUTES, minute);
        intent.putExtra(AlarmClock.EXTRA_MESSAGE, label != null ? label : "Jadwal Shift");
        intent.putExtra(AlarmClock.EXTRA_SKIP_UI, true);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);

        try {
            context.startActivity(intent);
            Toast.makeText(
                    context,
                    String.format(Locale.US, "Alarm disetel pukul %02d:%02d (1 jam sebelum shift)", hour, minute),
                    Toast.LENGTH_LONG
            ).show();
        } catch (Exception e) {
            Toast.makeText(context, "Gagal membuka aplikasi Jam/Alarm.", Toast.LENGTH_SHORT).show();
        }
    }

    private static PendingIntent refreshIntent(Context context) {
        Intent in = new Intent(context, PersonalWidgetProvider.class);
        in.setAction(ACTION_REFRESH);
        return PendingIntent.getBroadcast(
                context, 2, in, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    private static void scheduleNext(Context context) {
        AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (am == null) {
            return;
        }
        long now = System.currentTimeMillis();
        long next = Long.MAX_VALUE;
        for (Entry e : parse(prefs(context).getString(KEY_SCHEDULE, ""))) {
            if (e.start > now && e.start < next) next = e.start;
            if (e.end > now && e.end < next) next = e.end;
        }
        PendingIntent pi = refreshIntent(context);
        am.cancel(pi);
        if (next != Long.MAX_VALUE) {
            am.set(AlarmManager.RTC_WAKEUP, next + 1000L, pi);
        }
    }

    private static int idOf(Context context, String name) {
        return context.getResources().getIdentifier(name, "id", context.getPackageName());
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static boolean sameDay(long a, long b) {
        return fmt("yyyyMMdd", a).equals(fmt("yyyyMMdd", b));
    }

    private static String fmt(String pattern, long millis) {
        return new SimpleDateFormat(pattern, new Locale("id", "ID")).format(new Date(millis));
    }

    private static List<Entry> parse(String data) {
        List<Entry> out = new ArrayList<Entry>();
        if (data == null || data.length() == 0) {
            return out;
        }
        SimpleDateFormat f = new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.US);
        f.setLenient(false);
        for (String line : data.split("\n")) {
            String[] p = line.trim().split("\\|", -1);
            if (p.length < 4) continue;
            try {
                Entry e = new Entry();
                e.name = p[1].trim();
                e.hour = Integer.parseInt(p[2].trim());
                e.dur = Integer.parseInt(p[3].trim());
                e.start = f.parse(p[0].trim() + " " + String.format(Locale.US, "%02d:00", e.hour)).getTime();
                e.end = e.start + e.dur * HOUR_MS;
                out.add(e);
            } catch (Exception ignored) {
            }
        }
        return out;
    }
}
