package org.shiftapp.shiftapp;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.widget.RemoteViews;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * Widget homescreen "Jadwal Shift":
 *
 *   HARI INI 15-Nov            Time 17:29      (TextClock, jalan sendiri)
 *   SHIFT | Name   | Time | Name  | Time
 *   Duty: | Dirlan | 14+8 | Yasid | 14+8
 *   Next: | Cum    | 22:00|       |
 *
 * Data disimpan aplikasi Python (saveSchedule), satu baris per shift:
 *     yyyy-MM-dd|Nama|jamMulai|durasiJam        mis. 2026-11-15|Dirlan|14|8
 * Durasi (+8 / +5) sudah dihitung di Python. Widget hanya menentukan siapa
 * yang sedang bertugas dan siapa berikutnya, dan menjadwalkan pembaruan
 * sendiri tepat saat shift berganti, jadi tetap akurat walau aplikasi tertutup.
 */
public class ShiftWidgetProvider extends AppWidgetProvider {

    private static final String PREFS = "shift_widget";
    private static final String KEY_SCHEDULE = "schedule";
    private static final String ACTION_REFRESH = "org.shiftapp.shiftapp.REFRESH";
    private static final long HOUR_MS = 60L * 60L * 1000L;

    private static class Entry {
        String name;
        int hour;
        int dur;
        long start;
        long end;
    }

    // ------------------------------------------------------------ lifecycle
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
        if (intent != null && ACTION_REFRESH.equals(intent.getAction())) {
            updateAll(context);
        }
    }

    @Override
    public void onDisabled(Context context) {
        AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (am != null) {
            am.cancel(refreshIntent(context));
        }
    }

    // ------------------------------------------------- dipanggil dari Python
    public static void saveSchedule(Context context, String data) {
        SharedPreferences sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        sp.edit().putString(KEY_SCHEDULE, data == null ? "" : data).apply();
    }

    public static void updateAll(Context context) {
        AppWidgetManager manager = AppWidgetManager.getInstance(context);
        ComponentName cn = new ComponentName(context, ShiftWidgetProvider.class);
        int[] ids = manager.getAppWidgetIds(cn);
        for (int id : ids) {
            updateWidget(context, manager, id);
        }
        scheduleNext(context);
    }

    // -------------------------------------------------------------- tampilan
    private static void updateWidget(Context context, AppWidgetManager manager, int widgetId) {
        String pkg = context.getPackageName();
        int layoutId = context.getResources().getIdentifier("shift_widget", "layout", pkg);
        if (layoutId == 0) {
            return;
        }
        RemoteViews views = new RemoteViews(pkg, layoutId);

        String raw = prefs(context).getString(KEY_SCHEDULE, "");
        String[] c = compute(parse(raw), System.currentTimeMillis());

        setText(context, views, "duty_name1", c[0]);
        setText(context, views, "duty_time1", c[1]);
        setText(context, views, "duty_name2", c[2]);
        setText(context, views, "duty_time2", c[3]);
        setText(context, views, "next_name1", c[4]);
        setText(context, views, "next_time1", c[5]);
        setText(context, views, "next_name2", c[6]);
        setText(context, views, "next_time2", c[7]);

        Intent launch = context.getPackageManager().getLaunchIntentForPackage(pkg);
        if (launch != null) {
            PendingIntent pi = PendingIntent.getActivity(
                    context, 0, launch,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            views.setOnClickPendingIntent(idOf(context, "widget_root"), pi);
        }
        manager.updateAppWidget(widgetId, views);
    }

    private static void setText(Context context, RemoteViews views, String idName, String text) {
        views.setTextViewText(idOf(context, idName), text);
    }

    private static int idOf(Context context, String name) {
        return context.getResources().getIdentifier(name, "id", context.getPackageName());
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    // ------------------------------------------------ alarm pergantian shift
    private static PendingIntent refreshIntent(Context context) {
        Intent in = new Intent(context, ShiftWidgetProvider.class);
        in.setAction(ACTION_REFRESH);
        return PendingIntent.getBroadcast(
                context, 1, in, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    /** Alarm tidak-presisi (tanpa izin khusus): bisa meleset beberapa menit. */
    private static void scheduleNext(Context context) {
        AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (am == null) {
            return;
        }
        long now = System.currentTimeMillis();
        long next = Long.MAX_VALUE;
        for (Entry e : parse(prefs(context).getString(KEY_SCHEDULE, ""))) {
            if (e.start > now && e.start < next) {
                next = e.start;
            }
            if (e.end > now && e.end < next) {
                next = e.end;
            }
        }
        PendingIntent pi = refreshIntent(context);
        am.cancel(pi);
        if (next != Long.MAX_VALUE) {
            am.set(AlarmManager.RTC_WAKEUP, next + 1000L, pi);
        }
    }

    // ---------------------------------------------------------------- logika
    /**
     * Hasil: [duty nama1, duty waktu1, duty nama2, duty waktu2,
     *         next nama1, next waktu1, next nama2, next waktu2].
     * Aturan sama dengan compute() di schedule_logic.py.
     */
    static String[] compute(List<Entry> entries, long now) {
        if (entries.isEmpty()) {
            return new String[]{"-", "", "", "", "Buka app", "upload", "", ""};
        }

        List<String[]> duty = new ArrayList<String[]>();
        for (Entry e : entries) {
            if (e.start <= now && now < e.end) {
                duty.add(new String[]{e.name, e.hour + "+" + e.dur});
            }
        }

        long nextStart = Long.MAX_VALUE;
        for (Entry e : entries) {
            if (e.start > now && e.start < nextStart) {
                nextStart = e.start;
            }
        }
        List<String[]> next = new ArrayList<String[]>();
        if (nextStart != Long.MAX_VALUE) {
            String label = sameDay(nextStart, now)
                    ? fmt("HH:mm", nextStart)
                    : fmt("EEE HH:mm", nextStart);
            for (Entry e : entries) {
                if (e.start == nextStart) {
                    next.add(new String[]{e.name, label});
                }
            }
        }

        String[] d = slots(duty);
        String[] n = slots(next);
        return new String[]{d[0], d[1], d[2], d[3], n[0], n[1], n[2], n[3]};
    }

    /** Dua slot (nama, waktu). Jika lebih dari dua orang: "Nama +N" di slot kedua. */
    private static String[] slots(List<String[]> items) {
        if (items.isEmpty()) {
            return new String[]{"-", "", "", ""};
        }
        if (items.size() == 1) {
            return new String[]{items.get(0)[0], items.get(0)[1], "", ""};
        }
        String second = items.get(1)[0];
        if (items.size() > 2) {
            second = second + " +" + (items.size() - 2);
        }
        return new String[]{items.get(0)[0], items.get(0)[1], second, items.get(1)[1]};
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
            if (p.length < 4) {
                continue;
            }
            try {
                Entry e = new Entry();
                e.name = p[1].trim();
                e.hour = Integer.parseInt(p[2].trim());
                e.dur = Integer.parseInt(p[3].trim());
                e.start = f.parse(p[0].trim() + " " + String.format(Locale.US, "%02d:00", e.hour))
                        .getTime();
                e.end = e.start + e.dur * HOUR_MS;
                out.add(e);
            } catch (Exception ignored) {
                // baris rusak dilewati
            }
        }
        return out;
    }
}
