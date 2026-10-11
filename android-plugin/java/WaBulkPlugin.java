package com.example.wabulk;

import android.content.Context;
import android.content.Intent;
import android.provider.Settings;

import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

@CapacitorPlugin(name = "WaBulk")
public class WaBulkPlugin extends Plugin {

    @Override
    public void load() {
        SendQueue.listener = text -> {
            JSObject o = new JSObject();
            o.put("text", text);
            o.put("running", SendQueue.running);
            notifyListeners("status", o);
        };
    }

    @PluginMethod
    public void start(PluginCall call) {
        try {
            JSArray arr = call.getArray("targets");
            String message = call.getString("message", "");
            String app = call.getString("app", "biz");
            String image = call.getString("image", "");
            int min = call.getInt("min", 8);
            int max = call.getInt("max", 15);
            List<String[]> targets = new ArrayList<>();
            for (int i = 0; i < arr.length(); i++) {
                JSONObject o = arr.getJSONObject(i);
                targets.add(new String[]{o.optString("name", ""), o.getString("number")});
            }
            if (targets.isEmpty() || (message.trim().isEmpty() && image.isEmpty())) {
                call.reject("empty");
                return;
            }
            SendQueue.app = app;
            SendQueue.setImage(getContext().getApplicationContext(), image);
            SendQueue.start(getContext().getApplicationContext(), targets, message, min, max);
            call.resolve();
        } catch (Exception e) {
            call.reject(e.getMessage());
        }
    }

    @PluginMethod
    public void stop(PluginCall call) {
        SendQueue.stop();
        call.resolve();
    }

    @PluginMethod
    public void isAccessibilityEnabled(PluginCall call) {
        String enabled = Settings.Secure.getString(
                getContext().getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
        if (enabled == null) enabled = "";
        String pkg = getContext().getPackageName();
        boolean on = enabled.contains(pkg + "/" + WaService.class.getName())
                || enabled.contains(pkg + "/.WaService");
        JSObject o = new JSObject();
        o.put("enabled", on);
        o.put("running", SendQueue.running);
        o.put("text", SendQueue.status);
        call.resolve(o);
    }

    @PluginMethod
    public void openAccessibilitySettings(PluginCall call) {
        Intent i = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(i);
        call.resolve();
    }
}
