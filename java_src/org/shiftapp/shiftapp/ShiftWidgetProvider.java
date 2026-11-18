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

    public static void saveSchedule(Context context, String data) {
        SharedPreferences sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        sp.edit().putString(KEY_SCHEDULE, data == null ? "" : data).apply();
        PersonalWidgetProvider.updateAll(context);
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

    private static void updateWidget(Context context, AppWidgetManager manager, int widgetId) {
        String pkg = context.getPackageName();
        int layoutId = context.getResources().getIdentifier("shift_widget", "layout", pkg);
        if (layoutId == 0) {
            return;
        }
        RemoteViews views = new RemoteViews(pkg, layoutId);

        WidgetTheme.Palette th = WidgetTheme.load(context);
        WidgetTheme.bg(views, context, "widget_root", th.bg);
        WidgetTheme.bg(views, context, "w_header", th.card);
        WidgetTheme.fg(views, context, "w_title", th.text);
        WidgetTheme.fg(views, context, "w_date", th.nextBg);
        WidgetTheme.fg(views, context, "w_time_label", th.muted);
        WidgetTheme.fg(views, context, "w_time", th.text);

        WidgetTheme.bg(views, context, "w_duty_header", th.accent);
        WidgetTheme.fg(views, context, "w_duty_header", th.onAccent);
        WidgetTheme.bg(views, context, "w_next_header", th.nextBg);
        WidgetTheme.fg(views, context, "w_next_header", th.nextText);

        for (int i = 1; i <= 3; i++) {
            WidgetTheme.bg(views, context, "duty_row_" + i, th.card);
            WidgetTheme.fg(views, context, "duty_name" + i, th.text);
            WidgetTheme.fg(views, context, "duty_time" + i, th.accent2 != 0 ? th.accent2 : th.text);

            WidgetTheme.bg(views, context, "next_row_" + i, th.card);
            WidgetTheme.fg(views, context, "next_name" + i, th.text);
            WidgetTheme.fg(views, context, "next_time" + i, th.nextBg);
        }

        String raw = prefs(context).getString(KEY_SCHEDULE, "");
        String[] c = compute(parse(raw), System.currentTimeMillis());

        setText(context, views, "duty_name1", c[0]);
        setText(context, views, "duty_time1", c[1]);
        setText(context, views, "duty_name2", c[2]);
        setText(context, views, "duty_time2", c[3]);
        setText(context, views, "duty_name3", c[4]);
        setText(context, views, "duty_time3", c[5]);

        setText(context, views, "next_name1", c[6]);
        setText(context, views, "next_time1", c[7]);
        setText(context, views, "next_name2", c[8]);
        setText(context, views, "next_time2", c[9]);
        setText(context, views, "next_name3", c[10]);
        setText(context, views, "next_time3", c[11]);

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
        int id = idOf(context, idName);
        if (id != 0) {
            views.setTextViewText(id, text);
        }
    }

    private static int idOf(Context context, String name) {
        return context.getResources().getIdentifier(name, "id", context.getPackageName());
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static PendingIntent refreshIntent(Context context) {
        Intent in = new Intent(context, ShiftWidgetProvider.class);
        in.setAction(ACTION_REFRESH);
        return PendingIntent.getBroadcast(
                context, 1, in, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
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

    /**
     * Hasil 12 elemen:
     * [0..5]  = Duty 1..3 (nama, waktu)
     * [6..11] = Next 1..3 (nama, waktu HH:mm saja)
     */
    static String[] compute(List<Entry> entries, long now) {
        if (entries.isEmpty()) {
            return new String[]{
                    "1. -", "", "", "", "", "",
                    "1. Buka app", "upload", "", "", "", ""
            };
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
            // Bagian next cukup jam saja, tanpa hari dan tanggal
            String label = fmt("HH:mm", nextStart);
            for (Entry e : entries) {
                if (e.start == nextStart) {
                    next.add(new String[]{e.name, label});
                }
            }
        }

        String[] d = slots3(duty);
        String[] n = slots3(next);
        return new String[]{
                d[0], d[1], d[2], d[3], d[4], d[5],
                n[0], n[1], n[2], n[3], n[4], n[5]
        };
    }

    /** Maksimal 3 slot bernomor (1., 2., 3.). Jika > 3, baris ke-3 ditambah +N */
    private static String[] slots3(List<String[]> items) {
        if (items.isEmpty()) {
            return new String[]{"-", "", "", "", "", ""};
        }
        String n1 = "1. " + items.get(0)[0];
        String t1 = items.get(0)[1];

        String n2 = items.size() >= 2 ? "2. " + items.get(1)[0] : "";
        String t2 = items.size() >= 2 ? items.get(1)[1] : "";

        String n3 = "";
        String t3 = "";
        if (items.size() >= 3) {
            n3 = "3. " + items.get(2)[0];
            if (items.size() > 3) {
                n3 = n3 + " +" + (items.size() - 3);
            }
            t3 = items.get(2)[1];
        }
        return new String[]{n1, t1, n2, t2, n3, t3};
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