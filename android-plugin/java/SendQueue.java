package com.example.wabulk;

import android.accessibilityservice.AccessibilityService;
import android.content.ActivityNotFoundException;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** يدير طابور الإرسال: يفتح محادثة كل رقم، والخدمة تضغط زر الإرسال. */
public class SendQueue {

    public interface Listener { void onStatus(String text); }

    public static volatile boolean running = false;
    public static volatile boolean waiting = false;
    public static String status = "جاهز";
    public static Listener listener = null;

    private static List<String[]> targets = new ArrayList<>();
    private static String message = "";
    private static int idx = -1, ok = 0, failed = 0, minD = 8, maxD = 15;
    private static final Handler handler = new Handler(Looper.getMainLooper());
    private static Runnable timeout;
    private static final Random rnd = new Random();

    private static void update(String s) {
        status = s;
        handler.post(() -> { if (listener != null) listener.onStatus(s); });
    }

    public static void start(Context ctx, List<String[]> t, String msg, int mn, int mx) {
        targets = t; message = msg;
        minD = mn; maxD = Math.max(mn, mx);
        idx = -1; ok = 0; failed = 0;
        running = true;
        next(ctx);
    }

    public static void stop() {
        running = false; waiting = false;
        handler.removeCallbacksAndMessages(null);
        update("تم الإيقاف — تم: " + ok + " | فشل: " + failed);
    }

    private static void next(final Context ctx) {
        if (!running) return;
        idx++;
        if (idx >= targets.size()) { finish(ctx); return; }
        String[] c = targets.get(idx);
        update("(" + (idx + 1) + "/" + targets.size() + ") إرسال إلى " + (c[0].isEmpty() ? c[1] : c[0]));
        String text = message.replace("{name}", c[0]);
        openChat(ctx, Uri.parse("https://wa.me/" + c[1] + "?text=" + Uri.encode(text)));
        waiting = true;
        timeout = () -> {
            if (running && waiting) {      // لم يظهر زر الإرسال (رقم غير مسجل مثلاً)
                waiting = false;
                failed++;
                if (WaService.instance != null)
                    WaService.instance.performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK);
                scheduleNext(ctx);
            }
        };
        handler.postDelayed(timeout, 30000);
    }

    /** تستدعيها الخدمة بعد الضغط على زر الإرسال. */
    public static void onSent(Context ctx) {
        waiting = false;
        ok++;
        if (timeout != null) handler.removeCallbacks(timeout);
        scheduleNext(ctx);
    }

    private static void scheduleNext(final Context ctx) {
        if (!running) return;
        if (idx + 1 >= targets.size()) { next(ctx); return; }
        long d = (minD + rnd.nextInt(maxD - minD + 1)) * 1000L;
        handler.postDelayed(() -> next(ctx), d);
    }

    private static void finish(Context ctx) {
        running = false; waiting = false;
        update("انتهى — تم: " + ok + " | فشل: " + failed);
        Intent i = new Intent(ctx, MainActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
        ctx.startActivity(i);
    }

    private static void openChat(Context ctx, Uri uri) {
        String[] pkgs = {"com.whatsapp", "com.whatsapp.w4b", null};
        for (String pkg : pkgs) {
            try {
                Intent i = new Intent(Intent.ACTION_VIEW, uri).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                if (pkg != null) i.setPackage(pkg);
                ctx.startActivity(i);
                return;
            } catch (ActivityNotFoundException ignored) { }
        }
    }
}
