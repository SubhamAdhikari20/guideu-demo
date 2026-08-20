import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import '../../domain/entities/payment.dart';

class SandboxCheckoutPage extends StatefulWidget {
  const SandboxCheckoutPage({required this.payment, super.key});
  final Payment payment;

  @override
  State<SandboxCheckoutPage> createState() => _SandboxCheckoutPageState();
}

class _SandboxCheckoutPageState extends State<SandboxCheckoutPage> {
  late final WebViewController _controller;
  var _loading = true;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (_) { if (mounted) setState(() => _loading = true); },
        onPageFinished: (url) {
          if (!mounted) return;
          setState(() => _loading = false);
          if (url.contains('/payments/callbacks/')) Navigator.of(context).pop(true);
        },
      ));
    _loadCheckout();
  }

  void _loadCheckout() {
    final url = widget.payment.checkoutUrl!;
    final fields = widget.payment.checkoutPayload;
    if (fields == null || fields.isEmpty) {
      _controller.loadRequest(Uri.parse(url));
      return;
    }
    final inputs = fields.entries.map((entry) {
      final name = const HtmlEscape(HtmlEscapeMode.attribute).convert(entry.key);
      final value = const HtmlEscape(HtmlEscapeMode.attribute).convert(entry.value.toString());
      return '<input type="hidden" name="$name" value="$value">';
    }).join();
    final escapedUrl = const HtmlEscape(HtmlEscapeMode.attribute).convert(url);
    _controller.loadHtmlString('''<!doctype html><html><body><p>Opening secure provider checkout…</p><form id="payment" method="post" action="$escapedUrl">$inputs</form><script>document.getElementById('payment').submit();</script></body></html>''');
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text('${widget.payment.gateway} sandbox checkout')),
        body: Stack(children: [WebViewWidget(controller: _controller), if (_loading) const LinearProgressIndicator()]),
      );
}
