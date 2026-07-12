using System.Diagnostics;
using System.Reflection;
using System.Text.Json;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

namespace Sciwrix.Windows;

internal sealed class MainForm : Form
{
    private readonly WebView2 webView = new() { Dock = DockStyle.Fill };
    private readonly string? initialDocument;
    private string? currentDocumentPath;
    private MemoryStream? incomingSave;
    private string incomingName = "Sciwrix.md", incomingType = "text/markdown";
    private bool incomingSaveAs, pageReady;

    public MainForm(string? path)
    {
        initialDocument = IsDocument(path) ? Path.GetFullPath(path!) : null;
        Text = "Sciwrix"; Width = 1280; Height = 850; MinimumSize = new(720, 520);
        StartPosition = FormStartPosition.CenterScreen; AllowDrop = true; Controls.Add(webView);
        Load += async (_, _) => await InitialiseAsync(); DragEnter += OnDragEnter; DragDrop += OnDragDrop;
    }

    private async Task InitialiseAsync()
    {
        try
        {
            var appDirectory = ExtractWebApp();
            var profile = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Sciwrix", "WebView2");
            await webView.EnsureCoreWebView2Async(await CoreWebView2Environment.CreateAsync(userDataFolder: profile));
            var core = webView.CoreWebView2;
            core.Settings.AreDevToolsEnabled = false; core.Settings.IsStatusBarEnabled = false;
            core.WebMessageReceived += OnMessage; core.NavigationStarting += OnNavigationStarting; core.NewWindowRequested += OnNewWindowRequested;
            await core.AddScriptToExecuteOnDocumentCreatedAsync(ReadResource("Sciwrix.Windows.bridge.js"));
            core.NavigationCompleted += async (_, e) => { if (!e.IsSuccess || pageReady) return; pageReady = true; if (initialDocument is not null) await OpenAsync(initialDocument); };
            core.Navigate(new Uri(Path.Combine(appDirectory, "index.html")).AbsoluteUri);
        }
        catch (Exception ex)
        {
            MessageBox.Show(this, $"Sciwrix could not start.\n\n{ex.Message}\n\nEnsure Microsoft Edge WebView2 is installed.", "Sciwrix", MessageBoxButtons.OK, MessageBoxIcon.Error); Close();
        }
    }

    private static string ExtractWebApp()
    {
        var version = Assembly.GetExecutingAssembly().GetName().Version?.ToString(3) ?? "current";
        var directory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Sciwrix", "WebApp", version);
        Directory.CreateDirectory(directory);
        var path = Path.Combine(directory, "index.html");
        var embedded = ReadResource("Sciwrix.WebApp.index.html");
        if (!File.Exists(path) || new FileInfo(path).Length != System.Text.Encoding.UTF8.GetByteCount(embedded)) File.WriteAllText(path, embedded, new System.Text.UTF8Encoding(false));
        return directory;
    }

    private static string ReadResource(string name)
    {
        using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(name) ?? throw new InvalidOperationException($"Embedded resource {name} is missing.");
        using var reader = new StreamReader(stream); return reader.ReadToEnd();
    }

    private async void OnMessage(object? _, CoreWebView2WebMessageReceivedEventArgs args)
    {
        try
        {
            using var json = JsonDocument.Parse(args.WebMessageAsJson); var root = json.RootElement;
            switch (root.GetProperty("type").GetString())
            {
                case "open": ShowOpen(); break;
                case "new": currentDocumentPath = null; UpdateTitle(); break;
                case "print": webView.CoreWebView2.ShowPrintUI(CoreWebView2PrintDialogKind.System); break;
                case "save-begin":
                    incomingSave?.Dispose(); incomingSave = new(); incomingName = SafeName(root.GetProperty("name").GetString());
                    incomingType = root.GetProperty("mimeType").GetString() ?? "application/octet-stream"; incomingSaveAs = root.GetProperty("forceSaveAs").GetBoolean(); break;
                case "save-chunk" when incomingSave is not null:
                    await incomingSave.WriteAsync(Convert.FromBase64String(root.GetProperty("data").GetString() ?? "")); break;
                case "save-complete": CompleteSave(); break;
                case "save-failed": CancelSave(); MessageBox.Show(this, "Sciwrix could not prepare this file for saving.", "Sciwrix"); break;
            }
        }
        catch (Exception ex) { CancelSave(); MessageBox.Show(this, $"The Windows integration encountered a problem.\n\n{ex.Message}", "Sciwrix"); }
    }

    private void ShowOpen()
    {
        using var dialog = new OpenFileDialog { Title = "Open Markdown file", Filter = "Markdown files (*.md;*.markdown;*.txt)|*.md;*.markdown;*.txt|All files (*.*)|*.*" };
        if (dialog.ShowDialog(this) == DialogResult.OK) _ = OpenAsync(dialog.FileName);
    }

    private async Task OpenAsync(string path)
    {
        try
        {
            var payload = JsonSerializer.Serialize(new { name = Path.GetFileName(path), mimeType = "text/markdown", data = Convert.ToBase64String(await File.ReadAllBytesAsync(path)) });
            var result = await webView.CoreWebView2.ExecuteScriptAsync($"window.__sciwrixWindows.openDocument({payload})");
            if (!result.Contains("ok", StringComparison.OrdinalIgnoreCase)) throw new InvalidOperationException("The editor did not accept the document.");
            currentDocumentPath = Path.GetFullPath(path); UpdateTitle();
        }
        catch (Exception ex) { MessageBox.Show(this, $"Sciwrix could not open this file.\n\n{ex.Message}", "Sciwrix"); }
    }

    private void CompleteSave()
    {
        if (incomingSave is null) return;
        var markdown = IsMarkdown(incomingName, incomingType); var target = !incomingSaveAs && markdown ? currentDocumentPath : null;
        if (target is null)
        {
            using var dialog = new SaveFileDialog { Title = "Save Sciwrix document", FileName = incomingName, Filter = SaveFilter(incomingName), AddExtension = true, OverwritePrompt = true };
            if (dialog.ShowDialog(this) != DialogResult.OK) { CancelSave(); return; } target = dialog.FileName;
        }
        try
        {
            File.WriteAllBytes(target, incomingSave.ToArray());
            if (markdown) { currentDocumentPath = Path.GetFullPath(target); UpdateTitle(); }
            _ = webView.CoreWebView2.ExecuteScriptAsync($"window.__sciwrixWindows.showToast({JsonSerializer.Serialize($"Saved {Path.GetFileName(target)}")})");
        }
        catch (Exception ex) { MessageBox.Show(this, $"Sciwrix could not save this file.\n\n{ex.Message}", "Sciwrix"); }
        finally { CancelSave(); }
    }

    private void CancelSave() { incomingSave?.Dispose(); incomingSave = null; incomingSaveAs = false; }
    private void UpdateTitle() => Text = currentDocumentPath is null ? "Sciwrix" : $"{Path.GetFileName(currentDocumentPath)} — Sciwrix";
    private void OnNavigationStarting(object? _, CoreWebView2NavigationStartingEventArgs e) { if (Uri.TryCreate(e.Uri, UriKind.Absolute, out var uri) && uri.IsFile) return; e.Cancel = true; OpenExternal(e.Uri); }
    private void OnNewWindowRequested(object? _, CoreWebView2NewWindowRequestedEventArgs e) { e.Handled = true; OpenExternal(e.Uri); }
    private static void OpenExternal(string value) { if (Uri.TryCreate(value, UriKind.Absolute, out var uri) && (uri.Scheme == "http" || uri.Scheme == "https")) Process.Start(new ProcessStartInfo(value) { UseShellExecute = true }); }
    private void OnDragEnter(object? _, DragEventArgs e) { if (e.Data?.GetData(DataFormats.FileDrop) is string[] { Length: 1 } f && IsDocument(f[0])) e.Effect = DragDropEffects.Copy; }
    private void OnDragDrop(object? _, DragEventArgs e) { if (e.Data?.GetData(DataFormats.FileDrop) is string[] { Length: 1 } f && IsDocument(f[0])) _ = OpenAsync(f[0]); }
    private static bool IsDocument(string? path) => path is not null && File.Exists(path) && new[] { ".md", ".markdown", ".txt" }.Contains(Path.GetExtension(path), StringComparer.OrdinalIgnoreCase);
    private static bool IsMarkdown(string name, string type) => new[] { ".md", ".markdown", ".txt" }.Contains(Path.GetExtension(name), StringComparer.OrdinalIgnoreCase) || type.Contains("markdown", StringComparison.OrdinalIgnoreCase) || type.Equals("text/plain", StringComparison.OrdinalIgnoreCase);
    private static string SafeName(string? name) { var safe = string.IsNullOrWhiteSpace(name) ? "Sciwrix.md" : name.Trim(); foreach (var c in Path.GetInvalidFileNameChars()) safe = safe.Replace(c, '_'); return safe; }
    private static string SaveFilter(string name) => Path.GetExtension(name).ToLowerInvariant() switch { ".html" or ".htm" => "HTML document (*.html)|*.html|All files (*.*)|*.*", ".tex" => "LaTeX document (*.tex)|*.tex|All files (*.*)|*.*", _ => "Markdown document (*.md)|*.md|All files (*.*)|*.*" };
}
