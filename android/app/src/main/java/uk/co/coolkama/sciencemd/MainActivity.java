package uk.co.coolkama.sciencemd;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintManager;
import android.provider.OpenableColumns;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;

public final class MainActivity extends Activity {
    private static final int FILE_CHOOSER_REQUEST_CODE = 1001;

    private WebView webView;
    private ValueCallback<Uri[]> pendingFileSelection;
    private Uri pendingIncomingDocument;
    private boolean pageReady;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        captureIncomingDocument(getIntent());

        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);

        webView.addJavascriptInterface(new AndroidBridge(), "AndroidBridge");

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("file".equalsIgnoreCase(uri.getScheme())) {
                    return false;
                }

                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (ActivityNotFoundException exception) {
                    Toast.makeText(MainActivity.this, "No application can open this link.", Toast.LENGTH_SHORT).show();
                }
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                pageReady = true;
                view.evaluateJavascript(
                    "window.print = function () { AndroidBridge.printPage(); };",
                    null
                );
                openPendingIncomingDocument();
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(
                WebView view,
                ValueCallback<Uri[]> filePathCallback,
                FileChooserParams fileChooserParams
            ) {
                if (pendingFileSelection != null) {
                    pendingFileSelection.onReceiveValue(null);
                }
                pendingFileSelection = filePathCallback;

                Intent pickerIntent = createFilePickerIntent(fileChooserParams);

                try {
                    startActivityForResult(pickerIntent, FILE_CHOOSER_REQUEST_CODE);
                    return true;
                } catch (ActivityNotFoundException exception) {
                    pendingFileSelection = null;
                    Toast.makeText(MainActivity.this, "No file picker is available.", Toast.LENGTH_SHORT).show();
                    return false;
                }
            }
        });

        if (savedInstanceState == null) {
            webView.loadUrl("file:///android_asset/index.html");
        } else {
            webView.restoreState(savedInstanceState);
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        captureIncomingDocument(intent);
        openPendingIncomingDocument();
    }

    private void captureIncomingDocument(Intent intent) {
        if (intent == null) {
            return;
        }

        String action = intent.getAction();
        if (!Intent.ACTION_VIEW.equals(action) && !Intent.ACTION_EDIT.equals(action)) {
            return;
        }

        Uri uri = intent.getData();
        if (uri != null) {
            pendingIncomingDocument = uri;
        }
    }

    private void openPendingIncomingDocument() {
        if (!pageReady || pendingIncomingDocument == null) {
            return;
        }

        Uri uri = pendingIncomingDocument;
        pendingIncomingDocument = null;

        new Thread(() -> {
            try {
                byte[] contents = readAllBytes(uri);
                String fileName = resolveDisplayName(uri);
                String mimeType = getContentResolver().getType(uri);
                if (mimeType == null || mimeType.trim().isEmpty()) {
                    mimeType = "text/markdown";
                }

                String finalMimeType = mimeType;
                runOnUiThread(() -> injectMarkdownFile(contents, fileName, finalMimeType));
            } catch (Exception exception) {
                runOnUiThread(() -> Toast.makeText(
                    MainActivity.this,
                    "ScienceMD could not open this Markdown file.",
                    Toast.LENGTH_LONG
                ).show());
            }
        }).start();
    }

    private byte[] readAllBytes(Uri uri) throws IOException {
        try (
            InputStream input = getContentResolver().openInputStream(uri);
            ByteArrayOutputStream output = new ByteArrayOutputStream()
        ) {
            if (input == null) {
                throw new IOException("The selected document could not be read.");
            }

            byte[] buffer = new byte[8192];
            int read;
            while ((read = input.read(buffer)) != -1) {
                output.write(buffer, 0, read);
            }
            return output.toByteArray();
        }
    }

    private String resolveDisplayName(Uri uri) {
        String fileName = null;

        try (Cursor cursor = getContentResolver().query(
            uri,
            new String[] { OpenableColumns.DISPLAY_NAME },
            null,
            null,
            null
        )) {
            if (cursor != null && cursor.moveToFirst()) {
                int nameColumn = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (nameColumn >= 0) {
                    fileName = cursor.getString(nameColumn);
                }
            }
        } catch (Exception ignored) {
            // Fall back to the URI path below.
        }

        if (fileName == null || fileName.trim().isEmpty()) {
            fileName = uri.getLastPathSegment();
        }
        if (fileName == null || fileName.trim().isEmpty()) {
            fileName = "document.md";
        }

        return fileName;
    }

    private void injectMarkdownFile(byte[] contents, String fileName, String mimeType) {
        String encodedContents = Base64.encodeToString(contents, Base64.NO_WRAP);

        String script =
            "(function(){try{" +
            "var binary=atob(" + JSONObject.quote(encodedContents) + ");" +
            "var bytes=new Uint8Array(binary.length);" +
            "for(var i=0;i<binary.length;i++){bytes[i]=binary.charCodeAt(i);}" +
            "var file=new File([bytes]," + JSONObject.quote(fileName) + ",{type:" + JSONObject.quote(mimeType) + "});" +
            "var inputs=Array.prototype.slice.call(document.querySelectorAll('input[type=\"file\"]'));" +
            "var input=inputs.find(function(element){" +
            "var accept=(element.getAttribute('accept')||'').toLowerCase();" +
            "return accept.indexOf('image/')===-1&&(accept.indexOf('.md')!==-1||accept.indexOf('markdown')!==-1||accept.indexOf('text/plain')!==-1);" +
            "});" +
            "if(!input){input=inputs.find(function(element){return (element.getAttribute('accept')||'').toLowerCase().indexOf('image/')===-1;});}" +
            "if(!input){return 'no-input';}" +
            "var transfer=new DataTransfer();" +
            "transfer.items.add(file);" +
            "input.files=transfer.files;" +
            "input.dispatchEvent(new Event('change',{bubbles:true}));" +
            "return 'ok';" +
            "}catch(error){return 'error:'+error.message;}})();";

        webView.evaluateJavascript(script, result -> {
            if (result == null || result.contains("no-input") || result.contains("error:")) {
                Toast.makeText(
                    MainActivity.this,
                    "ScienceMD could not pass this file to the editor.",
                    Toast.LENGTH_LONG
                ).show();
                return;
            }

            Toast.makeText(
                MainActivity.this,
                "Opened " + fileName,
                Toast.LENGTH_SHORT
            ).show();
        });
    }

    private Intent createFilePickerIntent(WebChromeClient.FileChooserParams fileChooserParams) {
        if (isImageChooser(fileChooserParams.getAcceptTypes())) {
            return fileChooserParams.createIntent();
        }

        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.putExtra(
            Intent.EXTRA_MIME_TYPES,
            new String[] {
                "text/markdown",
                "text/x-markdown",
                "text/plain",
                "application/octet-stream"
            }
        );
        intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, false);

        return Intent.createChooser(intent, "Open Markdown file");
    }

    private boolean isImageChooser(String[] acceptTypes) {
        if (acceptTypes == null) {
            return false;
        }

        for (String acceptType : acceptTypes) {
            if (acceptType != null && acceptType.startsWith("image/")) {
                return true;
            }
        }

        return false;
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode != FILE_CHOOSER_REQUEST_CODE || pendingFileSelection == null) {
            return;
        }

        Uri[] result = resultCode == RESULT_OK
            ? WebChromeClient.FileChooserParams.parseResult(resultCode, data)
            : null;

        pendingFileSelection.onReceiveValue(result);
        pendingFileSelection = null;
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        webView.saveState(outState);
        super.onSaveInstanceState(outState);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    private void printScienceMdDocument() {
        PrintManager printManager = (PrintManager) getSystemService(PRINT_SERVICE);
        PrintDocumentAdapter adapter = webView.createPrintDocumentAdapter("ScienceMD document");
        printManager.print(
            "ScienceMD document",
            adapter,
            new PrintAttributes.Builder().build()
        );
    }

    private final class AndroidBridge {
        @JavascriptInterface
        public void printPage() {
            runOnUiThread(MainActivity.this::printScienceMdDocument);
        }
    }
}
