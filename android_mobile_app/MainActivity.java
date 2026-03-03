package com.example.smartparking;

import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WebView webView = new WebView(this);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        String webAppUrl = BuildConfig.DEBUG
            ? "http://10.0.2.2:5000/login"
            : "https://YOUR-RENDER-APP.onrender.com/login";
        webView.loadUrl(webAppUrl);
        setContentView(webView);
    }
}
