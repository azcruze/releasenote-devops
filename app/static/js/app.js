// Progressive enhancement only: every feature works without JavaScript.
(function () {
  var toggle = document.querySelector('.nav-toggle');
  var sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', function () {
      var open = sidebar.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
  }
  document.querySelectorAll('.flash-close').forEach(function (btn) {
    btn.addEventListener('click', function () { btn.closest('.flash').remove(); });
  });
  document.querySelectorAll('.filters select').forEach(function (sel) {
    sel.addEventListener('change', function () { sel.form.submit(); });
  });

  var dashboard = document.querySelector('.analytics-grid');
  var filterForm = document.getElementById('dashboard-filters');
  if (!dashboard || !filterForm) return;

  var endpoint = '/api/dashboard';
  var activeMonth = new Date().toISOString().slice(0, 7);
  var palette = {
    Released: '#69bfa8',
    Scheduled: '#79a9ee',
    Draft: '#a7b0c3',
    'Rolled Back': '#f19191',
    Deprecated: '#edbd72'
  };
  var typePalette = { Major: '#8a8be8', Minor: '#70b9d3', Patch: '#70c1a7' };
  var statusOrder = ['Released', 'Scheduled', 'Draft', 'Rolled Back', 'Deprecated'];
  var typeOrder = ['Major', 'Minor', 'Patch'];
  var statusChart = document.getElementById('status-chart');
  var lineChart = document.getElementById('monthly-chart');
  var typeChart = document.getElementById('types-chart');
  var statusLegend = document.getElementById('status-legend');
  var calendarDays = document.getElementById('calendar-days');
  var calendarTitle = document.getElementById('calendar-month');
  var feedback = document.getElementById('dashboard-feedback');
  var refreshButton = document.getElementById('dashboard-refresh');
  var requestNumber = 0;
  var svgNs = 'http://www.w3.org/2000/svg';

  function svgNode(tag, attrs, text) {
    var node = document.createElementNS(svgNs, tag);
    Object.keys(attrs || {}).forEach(function (key) { node.setAttribute(key, attrs[key]); });
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function setText(selector, value) {
    var node = document.querySelector(selector);
    if (node) node.textContent = String(value);
  }

  function prettyDate(value) {
    var parts = value.split('-');
    var date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    return date.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function monthLabel(value) {
    var parts = value.split('-');
    return new Date(Number(parts[0]), Number(parts[1]) - 1, 1)
      .toLocaleDateString(undefined, { month: 'short', year: '2-digit' });
  }

  function drawMonthlyChart(data) {
    lineChart.replaceChildren();
    lineChart.setAttribute('viewBox', '0 0 640 230');
    var empty = lineChart.parentElement.querySelector('.chart-empty');
    var hasValues = data.monthly_counts.some(function (count) { return count > 0; });
    empty.hidden = hasValues;
    lineChart.hidden = !hasValues;
    if (!hasValues) return;

    var width = 640, height = 230, left = 38, right = 15, top = 15, bottom = 38;
    var values = data.monthly_counts;
    var maximum = Math.max.apply(null, values.concat([1]));
    var count = values.length;
    var x = function (i) { return count === 1 ? (left + width - right) / 2 : left + i * (width - left - right) / (count - 1); };
    var y = function (value) { return height - bottom - (value / maximum) * (height - top - bottom); };
    var defs = svgNode('defs');
    var gradient = svgNode('linearGradient', { id: 'release-line-fill', x1: '0', x2: '0', y1: '0', y2: '1' });
    gradient.append(svgNode('stop', { offset: '0%', 'stop-color': '#a9c7f0', 'stop-opacity': '.42' }));
    gradient.append(svgNode('stop', { offset: '100%', 'stop-color': '#eaf4ff', 'stop-opacity': '.08' }));
    defs.appendChild(gradient);
    lineChart.appendChild(defs);

    for (var tick = 0; tick <= 3; tick += 1) {
      var tickValue = Math.ceil(maximum * tick / 3);
      var tickY = y(tickValue);
      lineChart.appendChild(svgNode('line', { x1: left, x2: width - right, y1: tickY, y2: tickY, class: 'chart-gridline' }));
      lineChart.appendChild(svgNode('text', { x: left - 10, y: tickY + 4, 'text-anchor': 'end', class: 'chart-axis-label' }, String(tickValue)));
    }

    var points = values.map(function (value, index) { return x(index) + ',' + y(value); });
    var area = 'M ' + x(0) + ' ' + (height - bottom) + ' L ' +
      values.map(function (value, index) { return x(index) + ' ' + y(value); }).join(' L ') +
      ' L ' + x(count - 1) + ' ' + (height - bottom) + ' Z';
    lineChart.appendChild(svgNode('path', { d: area, class: 'chart-area' }));
    lineChart.appendChild(svgNode('polyline', { points: points.join(' '), class: 'chart-line' }));

    values.forEach(function (value, index) {
      var dot = svgNode('circle', { cx: x(index), cy: y(value), r: 4, class: 'chart-point', tabindex: '0' });
      dot.appendChild(svgNode('title', {}, monthLabel(data.months[index]) + ': ' + value + ' release' + (value === 1 ? '' : 's')));
      lineChart.appendChild(dot);
      if (count <= 12 || index === 0 || index === count - 1 || index % Math.ceil(count / 8) === 0) {
        lineChart.appendChild(svgNode('text', { x: x(index), y: height - 10, 'text-anchor': 'middle', class: 'chart-axis-label' }, monthLabel(data.months[index])));
      }
    });
    lineChart.setAttribute('aria-label', 'Monthly release activity from ' + data.start_date + ' to ' + data.end_date);
  }

  function drawStatusChart(data) {
    statusChart.replaceChildren();
    statusChart.setAttribute('viewBox', '0 0 180 180');
    var values = statusOrder.map(function (key) { return { name: key, count: data.filtered_status_counts[key] || 0 }; });
    var total = values.reduce(function (sum, item) { return sum + item.count; }, 0);
    setText('[data-donut-total]', total);
    statusLegend.replaceChildren();
    if (!total) {
      statusChart.hidden = true;
      statusLegend.appendChild(emptyListItem('No status data for this view.'));
      return;
    }
    statusChart.hidden = false;
    var radius = 63;
    var circumference = 2 * Math.PI * radius;
    var offset = 0;
    values.forEach(function (item) {
      if (!item.count) return;
      var segment = circumference * item.count / total;
      var circle = svgNode('circle', {
        cx: 90, cy: 90, r: radius, class: 'donut-segment',
        stroke: palette[item.name], 'stroke-dasharray': segment + ' ' + (circumference - segment),
        'stroke-dashoffset': -offset, transform: 'rotate(-90 90 90)', tabindex: '0'
      });
      circle.appendChild(svgNode('title', {}, item.name + ': ' + item.count + ' (' + Math.round(item.count * 100 / total) + '%)'));
      statusChart.appendChild(circle);
      offset += segment;

      var entry = document.createElement('li');
      var swatch = document.createElement('span');
      swatch.className = 'legend-swatch';
      swatch.style.backgroundColor = palette[item.name];
      var link = document.createElement('a');
      link.href = '/releases?status=' + encodeURIComponent(item.name);
      link.textContent = item.name;
      var amount = document.createElement('strong');
      amount.textContent = String(item.count);
      entry.append(swatch, link, amount);
      statusLegend.appendChild(entry);
    });
  }

  function drawTypeChart(data) {
    typeChart.replaceChildren();
    typeChart.setAttribute('viewBox', '0 0 560 178');
    var empty = typeChart.parentElement.querySelector('.chart-empty');
    var values = typeOrder.map(function (name) { return { name: name, count: data.category_counts[name] || 0 }; });
    var max = Math.max.apply(null, values.map(function (item) { return item.count; }).concat([1]));
    var any = values.some(function (item) { return item.count > 0; });
    typeChart.hidden = !any;
    empty.hidden = any;
    if (!any) return;

    values.forEach(function (item, index) {
      var y = 22 + index * 52;
      typeChart.appendChild(svgNode('text', { x: 0, y: y + 14, class: 'bar-label' }, item.name));
      typeChart.appendChild(svgNode('rect', { x: 88, y: y, width: 420, height: 20, rx: 10, class: 'bar-track' }));
      var barWidth = item.count ? Math.max(5, 420 * item.count / max) : 0;
      var anchor = svgNode('a', { href: '/releases?category=' + encodeURIComponent(item.name), class: 'chart-bar-link' });
      var bar = svgNode('rect', { x: 88, y: y, width: barWidth, height: 20, rx: 10, fill: typePalette[item.name], class: 'chart-bar' });
      bar.appendChild(svgNode('title', {}, item.name + ': ' + item.count + ' release' + (item.count === 1 ? '' : 's')));
      anchor.appendChild(bar);
      typeChart.appendChild(anchor);
      typeChart.appendChild(svgNode('text', { x: 526, y: y + 15, class: 'bar-value' }, String(item.count)));
    });
  }

  function emptyListItem(message) {
    var item = document.createElement('li');
    item.className = 'widget-empty';
    item.textContent = message;
    return item;
  }

  function releaseStatusBadge(status) {
    var badge = document.createElement('span');
    badge.className = 'badge st-' + status.toLowerCase().replaceAll(' ', '-');
    badge.textContent = status;
    return badge;
  }

  function renderRecent(items) {
    var list = document.getElementById('recent-releases');
    list.replaceChildren();
    if (!items.length) {
      list.appendChild(emptyListItem('No releases match the selected filters.'));
      return;
    }
    items.forEach(function (release) {
      var link = document.createElement('a');
      link.className = 'activity-item';
      link.href = '/releases/' + release.id;
      var version = document.createElement('span');
      version.className = 'activity-version ver';
      version.textContent = 'v' + release.version;
      var copy = document.createElement('span');
      copy.className = 'activity-copy';
      var title = document.createElement('strong');
      title.textContent = release.title;
      var date = document.createElement('small');
      date.textContent = prettyDate(release.release_date);
      copy.append(title, date);
      link.append(version, copy, releaseStatusBadge(release.status));
      list.appendChild(link);
    });
  }

  function renderUpcoming(items) {
    var list = document.getElementById('upcoming-releases');
    list.replaceChildren();
    if (!items.length) {
      list.appendChild(emptyListItem('No upcoming scheduled releases.'));
      return;
    }
    items.forEach(function (release) {
      var link = document.createElement('a');
      link.className = 'upcoming-item';
      link.href = '/releases/' + release.id;
      var dateParts = release.release_date.split('-');
      var date = document.createElement('span');
      date.className = 'upcoming-date';
      var day = document.createElement('strong');
      day.textContent = dateParts[2];
      var month = document.createElement('small');
      month.textContent = new Date(Number(dateParts[0]), Number(dateParts[1]) - 1, 1)
        .toLocaleDateString(undefined, { month: 'short' });
      date.append(day, month);
      var copy = document.createElement('span');
      copy.className = 'upcoming-copy';
      var title = document.createElement('strong');
      title.textContent = 'v' + release.version + ' ' + release.title;
      var fullDate = document.createElement('small');
      fullDate.textContent = prettyDate(release.release_date);
      copy.append(title, fullDate);
      var arrow = document.createElement('span');
      arrow.className = 'upcoming-arrow';
      arrow.setAttribute('aria-hidden', 'true');
      arrow.textContent = '↗';
      link.append(date, copy, arrow);
      list.appendChild(link);
    });
  }

  function renderCalendar(calendar) {
    calendarTitle.textContent = calendar.month_name;
    calendarDays.replaceChildren();
    for (var blank = 0; blank < calendar.first_weekday; blank += 1) {
      var spacer = document.createElement('span');
      spacer.className = 'calendar-day is-blank';
      spacer.setAttribute('aria-hidden', 'true');
      calendarDays.appendChild(spacer);
    }
    var releasesByDate = {};
    calendar.scheduled.forEach(function (release) {
      releasesByDate[release.release_date] = releasesByDate[release.release_date] || [];
      releasesByDate[release.release_date].push(release);
    });
    for (var day = 1; day <= calendar.days_in_month; day += 1) {
      var isoDate = calendar.year + '-' + String(calendar.month).padStart(2, '0') + '-' + String(day).padStart(2, '0');
      var cell = document.createElement('div');
      cell.className = 'calendar-day';
      cell.setAttribute('role', 'listitem');
      cell.dataset.calendarDate = isoDate;
      var dayNumber = document.createElement('span');
      dayNumber.textContent = String(day);
      cell.appendChild(dayNumber);
      (releasesByDate[isoDate] || []).forEach(function (release) {
        cell.classList.add('has-release');
        var link = document.createElement('a');
        link.className = 'calendar-dot';
        link.href = '/releases/' + release.id;
        link.title = 'v' + release.version + ' — ' + release.title;
        link.setAttribute('aria-label', 'v' + release.version + ' ' + release.title);
        cell.appendChild(link);
      });
      calendarDays.appendChild(cell);
    }
  }

  function updateKpis(data) {
    setText('[data-kpi="total"]', data.total);
    statusOrder.forEach(function (name) {
      setText('[data-kpi-status="' + name + '"]', data.status_counts[name] || 0);
    });
  }

  async function refreshDashboard(updateAddress) {
    var currentRequest = ++requestNumber;
    var query = new URLSearchParams(new FormData(filterForm));
    if (activeMonth) query.set('month', activeMonth);
    feedback.textContent = 'Refreshing release data…';
    refreshButton.disabled = true;
    dashboard.setAttribute('aria-busy', 'true');
    try {
      var response = await fetch(endpoint + '?' + query.toString(), {
        headers: { Accept: 'application/json' },
        cache: 'no-store'
      });
      var result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Dashboard data could not be loaded.');
      if (currentRequest !== requestNumber) return;
      updateKpis(result);
      drawMonthlyChart(result);
      drawStatusChart(result);
      drawTypeChart(result);
      renderRecent(result.recent);
      renderUpcoming(result.upcoming);
      renderCalendar(result.calendar);
      if (updateAddress) {
        query.delete('month');
        var queryString = query.toString();
        history.replaceState(null, '', queryString ? '/?' + queryString : '/');
      }
      feedback.textContent = '';
    } catch (error) {
      if (currentRequest === requestNumber) feedback.textContent = error.message;
    } finally {
      if (currentRequest === requestNumber) {
        refreshButton.disabled = false;
        dashboard.removeAttribute('aria-busy');
      }
    }
  }

  filterForm.addEventListener('submit', function (event) {
    event.preventDefault();
    refreshDashboard(true);
  });
  filterForm.querySelectorAll('select,input[type="date"]').forEach(function (control) {
    control.addEventListener('change', function () { refreshDashboard(true); });
  });
  var searchTimer;
  filterForm.querySelector('input[name="q"]').addEventListener('input', function () {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(function () { refreshDashboard(true); }, 300);
  });
  refreshButton.addEventListener('click', function () { refreshDashboard(false); });
  document.querySelectorAll('.calendar-move').forEach(function (button) {
    button.addEventListener('click', function () {
      var parts = activeMonth.split('-');
      var date = new Date(Number(parts[0]), Number(parts[1]) - 1 + Number(button.dataset.monthStep), 1);
      activeMonth = date.getFullYear() + '-' + String(date.getMonth() + 1).padStart(2, '0');
      refreshDashboard(false);
    });
  });

  refreshDashboard(false);
})();
