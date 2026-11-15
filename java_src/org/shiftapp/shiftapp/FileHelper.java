package org.shiftapp.shiftapp;

import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.provider.OpenableColumns;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/** Menyalin file pilihan pengguna (content://) ke cache aplikasi agar bisa dibaca Python. */
public class FileHelper {

    public static String copyToCache(Context context, Uri uri) throws IOException {
        String name = "jadwal";
        Cursor cursor = context.getContentResolver().query(uri, null, null, null, null);
        try {
            if (cursor != null && cursor.moveToFirst()) {
                int idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (idx >= 0) {
                    String n = cursor.getString(idx);
                    if (n != null && n.length() > 0) {
                        name = n;
                    }
                }
            }
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
        name = name.replaceAll("[^A-Za-z0-9._-]", "_");

        File out = new File(context.getCacheDir(), name);
        InputStream in = context.getContentResolver().openInputStream(uri);
        if (in == null) {
            throw new IOException("Tidak bisa membuka file");
        }
        try {
            OutputStream os = new FileOutputStream(out);
            try {
                byte[] buf = new byte[8192];
                int n;
                while ((n = in.read(buf)) > 0) {
                    os.write(buf, 0, n);
                }
            } finally {
                os.close();
            }
        } finally {
            in.close();
        }
        return out.getAbsolutePath();
    }
}
