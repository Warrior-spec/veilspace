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
  final Map<String, int> _failures = {};

  File _preference(String account) {
    final base =
        Platform.environment['LOCALAPPDATA'] ?? Directory.systemTemp.path;
    return File(
        '$base/VeilSpace/watch-${sha256.convert(utf8.encode(account.toLowerCase()))}.txt');
  }

  Future<String?> savedFolder(String account) async {
    try {
      return await _preference(account).readAsString();
    } catch (_) {
      return null;
    }
  }

  Future<void> saveFolder(String account, String? path) async {
    final file = _preference(account);
    if (path == null) {
      if (await file.exists()) await file.delete();
      return;
    }
    await file.parent.create(recursive: true);
    await file.writeAsString(path, flush: true);
  }

  Future<void> start(
      String path,
      Future<void> Function(String, List<int>, String) upload,
      void Function(String) report) async {
    stop();
    final generation = _generation;
    _sent.clear();
    _stable.clear();
    _failures.clear();
    Future<void> scan() async {
      if (_busy || generation != _generation) return;
      _busy = true;
      try {
        await for (final entry in Directory(path).list(followLinks: false)) {
          if (generation != _generation) break;
          if (entry is! File ||
              !RegExp(r'\.(txt|pdf|docx)$', caseSensitive: false)
                  .hasMatch(entry.path)) {
            continue;
          }
          try {
            final stat = await entry.stat();
            if (stat.size > 10485760 || stat.size == 0) continue;
            final stamp =
                '${stat.size}:${stat.modified.microsecondsSinceEpoch}';
            if (_stable[entry.path] != stamp) {
              _stable[entry.path] = stamp;
              _failures[entry.path] = 0;
              continue;
            }
            if (_sent[entry.path] == stamp) continue;
            if ((_failures[entry.path] ?? 0) >= 3) continue;
            final bytes = await entry.readAsBytes();
            final after = await entry.stat();
            if (after.size != stat.size ||
                after.modified != stat.modified ||
                generation != _generation) {
              continue;
            }
            await upload(
                entry.uri.pathSegments.last,
                bytes,
                sha256
                    .convert(utf8.encode(entry.absolute.path.toLowerCase()))
                    .toString());
            _sent[entry.path] = stamp;
          } catch (_) {
            final attempts = (_failures[entry.path] ?? 0) + 1;
            _failures[entry.path] = attempts;
            if (attempts == 3) {
              report(
                  'A watched file failed three uploads. Edit it or select the folder again to retry.');
            }
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
