package com.example.wabulk;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.os.Handler;
import android.os.Looper;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import java.util.List;

public class WaService extends AccessibilityService {

    public static WaService instance;
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override
    protected void onServiceConnected() { instance = this; }

    @Override
    public boolean onUnbind(Intent intent) {
        instance = null;
        return super.onUnbind(intent);
    }

    @Override
    public void onInterrupt() { }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (!SendQueue.running || !SendQueue.waiting) return;
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null || findSend(root) == null) return;

        SendQueue.waiting = false;   // يمنع الضغط المتكرر
        handler.postDelayed(() -> {
            AccessibilityNodeInfo r = getRootInActiveWindow();
            AccessibilityNodeInfo btn = (r == null) ? null : findSend(r);
            if (btn != null && clickNode(btn)) {
                SendQueue.onSent(getApplicationContext());
            } else {
                SendQueue.waiting = true;
            }
        }, 1000);
    }

    private AccessibilityNodeInfo findSend(AccessibilityNodeInfo root) {
        String[] ids = {"com.whatsapp:id/send", "com.whatsapp.w4b:id/send"};
        for (String id : ids) {
            List<AccessibilityNodeInfo> l = root.findAccessibilityNodeInfosByViewId(id);
            if (l != null && !l.isEmpty()) return l.get(0);
        }
        String[] labels = {"Send", "إرسال"};
        for (String label : labels) {
            List<AccessibilityNodeInfo> l = root.findAccessibilityNodeInfosByText(label);
            if (l == null) continue;
            for (AccessibilityNodeInfo n : l) {
                if (n.isClickable() || (n.getParent() != null && n.getParent().isClickable())) return n;
            }
        }
        return null;
    }

    private boolean clickNode(AccessibilityNodeInfo node) {
        AccessibilityNodeInfo n = node;
        while (n != null) {
            if (n.isClickable()) return n.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            n = n.getParent();
        }
        return false;
    }
}
