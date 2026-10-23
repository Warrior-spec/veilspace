import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';

class FolderWatch {
  Timer? _timer;
  bool _busy = false;
  int _generation = 0;
  final Map<String, String> _sent = {};
  final Map<String, String> _stable = {};

  Future<void> start(String path, Future<void> Function(String, List<int>, String) upload, void Function(String) report) async {
    stop();
    final generation = _generation;
    _sent.clear();
    _stable.clear();
    Future<void> scan() async {
      if (_busy || generation != _generation) return;
      _busy = true;
      try {
        await for (final entry in Directory(path).list(followLinks: false)) {
          if (generation != _generation) break;
          if (entry is! File || !RegExp(r'\.(txt|pdf|docx)$', caseSensitive: false).hasMatch(entry.path)) continue;
          try {
            final stat = await entry.stat();
            if (stat.size > 10485760 || stat.size == 0) continue;
            final stamp = '${stat.size}:${stat.modified.microsecondsSinceEpoch}';
            if (_stable[entry.path] != stamp) {
              _stable[entry.path] = stamp;
              continue;
            }
            if (_sent[entry.path] == stamp) continue;
            final bytes = await entry.readAsBytes();
            final after = await entry.stat();
            if (after.size != stat.size || after.modified != stat.modified || generation != _generation) continue;
            await upload(entry.uri.pathSegments.last, bytes, sha256.convert(utf8.encode(entry.absolute.path.toLowerCase())).toString());
            _sent[entry.path] = stamp;
          } catch (_) {
            report('A watched file could not upload. Retrying shortly.');
          }
        }
      } catch (_) {
        report('Watched folder is unavailable.');
      } finally {
        _busy = false;
      }
    }
    _timer = Timer.periodic(const Duration(seconds: 5), (_) => scan());
    await scan();
  }

  void stop() {
    _generation++;
    _timer?.cancel();
    _timer = null;
  }
}
